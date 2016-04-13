(function(_WIN) {
    function wGame(containerElement, boardConfig) {
        var _step = 0;
        var _myColor = WGo.B;
        var _wgoColor = WGo.W;
        var _isMyTurn = false;
        var _board;
        var maxBorder = 19;

        var Point = function(x,y){
            this.x = x;
            this.y = y;
        }
        var userInfo = {
            name:'',
            rank:''
        }
        // Robot round
        // Return new board
        var userStep = new Point(-1,-1);
        url = 'http://www.baidu.com';
        userInfo.name = 'jianqiang';
        userInfo.rank = 'wu';
        var url = 'http://suzvm-linux33:8080/move';
        function opponentRound() {
            var brainSuccessed = function(){
                _isMyTurn = true;
            }

            var brainFailed = function (){
                _isMyTurn = false;
            }
            // Get whold board -> post to server
            _step++;

            if(!_isMyTurn){
                $.when(brainStep(url,userInfo,userStep))
                    .done(brainSuccessed)
                    .fail(brainFailed);
            }

            // data: {name:'name', rank:userInfo.rank, x:userStep.x, y:userStep.y}, 
            function brainStep(url, userInfo, userStep){
                var deferred = $.Deferred();

                var successed = function(wgoStep){
                     _board.addObject({
                            x: wgoStep.x,
                            y: wgoStep.y,
                            c: _wgoColor
                        });
                     deferred.resolve();
                } 
                var failed = function(){
                            _board.addObject({
                            x: 1,
                            y: Math.floor(Math.random() * 2)%10,
                            c: _wgoColor
                        });
                    console.log('There is something wrong with server');
                    deferred.reject('There is something wrong with server');
                }
                
                $.ajax({
                    type: 'POST',
                    url: url,
                    data: JSON.stringify({
                        name: userInfo.name,
                        rank: userInfo.rank,
                        x: userStep.x,
                        y: userStep.y
                    }),
                    contentType: "application/json"
                })
                .done(successed)
                .fail(failed);

                return deferred.promise();
            }

        }

        function numberToAlphabet(numX,numY){
            if(numX >= maxBorder || numY >= maxBorder || numX < 0 || numY < 0){
                return ;
            }
            var base = 'a'.charCodeAt();
            var result = String.fromCharCode(numX + base) + String.fromCharCode(numY + base);
            return result;
        }

        function alphabetToNumber(strRes){
            if(strRes.length != 2){
                return ;
            }
            strRes = strRes.toLowerCase();
            var base = 'a'.charCodeAt();
            var numX = strRes[0].charCodeAt() - base; 
            var numY = strRes[1].charCodeAt() - base;
            if(numX < 0 || numY < 0 || numX >= maxBorder || numY >= maxBorder){
                return ;
            }
            return [numX,numY];
        }

        var self = {
            init: function() {
                var _this = this;

                // Create board
                _board = new WGo.Board(containerElement, boardConfig);
                _board.addEventListener("click", function(x, y) {
                    if (!_isMyTurn) {
                        return;
                    }
                    _step++;
                    userStep.x = x;
                    userStep.y = y;
                    // Add my stone to board
                    _board.addObject({
                        x: x,
                        y: y,
                        c: _myColor
                    });
                    _isMyTurn = false;
                    opponentRound();
                });

                // 0: black
                // 1: white
                _myColor = Math.floor(Math.random() * 2) ? WGo.W : WGo.B;
                if (_myColor === WGo.B) {
                    _isMyTurn = true;
                    _wgoColor = WGo.W;
                } else {
                    // Robot round
                    _isMyTurn = false;
                    _wgoColor = WGo.B;
                    opponentRound();
                }
            },
            getMyColor: function(){
                return _myColor;
            },
            getStep: function(){
                return _step;
            },
            getIsMyTurn: function(){
                return _isMyTurn;
            }
        };

        return self;
    }

    _WIN.wGame = wGame;
})(window);

var game = wGame(document.getElementById("board"), {
    width: 400,
});
game.init();
