
function RainbowSocks(server){
    this.server = server;
    this.triggers = {}
    this.requests = {}
}

RainbowSocks.prototype.trigger = function (trigger, callback){
    this.triggers[trigger] = callback;
}

RainbowSocks.prototype.start = function () {
    _rs = this;
    _rs.websocket = new WebSocket(_rs.server);
    _rs.websocket.onmessage = function (raw_event) {
        event = JSON.parse(raw_event.data);
        if(event.status == "broadcast"){
            if(event.trigger in _rs.triggers){
                _rs.triggers[event.trigger](_rs, event.data);
            }
        }else if(event.status == "reply"){
            if(event.eventid in _rs.requests){
                _rs.requests[event.eventid](_rs, event.data)
                delete _rs.requests[event.eventid];
            }
        }
        
    }
    return _rs;
}

RainbowSocks.prototype.request = function (trigger, data, callback){
    eventid = Math.floor(Math.random()*167772150000000).toString(16);
    this.requests[eventid] = callback;
    //payload = {"trigger": trigger, "data": data, "eventid": eventid}
    this.websocket.send(JSON.stringify({
        trigger: trigger,
        data: data, 
        eventid: eventid
    }));
}