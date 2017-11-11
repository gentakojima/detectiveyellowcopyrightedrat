// ==UserScript==
// @name         gymscraping
// @namespace    http://tampermonkey.net/
// @version      0.2
// @description  try to take over the world!
// @author       You
// @require http://code.jquery.com/jquery-1.12.4.min.js
// @require https://fastcdn.org/FileSaver.js/1.1.20151003/FileSaver.min.js
// @match        *gymhuntr.com*
// @grant        none
// ==/UserScript==

var spacer = Array(30).join("#");

// download a file on html5 ready browsers
var showDownloadButton = function(){
  var button = document.createElement("button");
  button.innerHTML = "Download Gyms CSV";
  button.style = "top:0;right:0;position:absolute;margin:20px;z-index: 9999";
  document.body.appendChild(button);
  $(button).click(function(){
    ohmylog("Click outside");
    if(window.CSV_GYMS){
      ohmylog("Click inside");
      var address = $("#address").val().split(" ").join("_") || "";
      var filename = "gyms" + ( address ? "_" + address : "") + "_" + new Date().getTime() + ".csv";
      var blob = new Blob([CSV_GYMS], {
        type: "text/plain;charset=utf-8"
      });
      saveAs(blob, filename);
    }
  });
};

(function() {
    'use strict';
    // save log and dir
    ohmylog = window.ohmylog = console.log;
    ohmydir = window.ohmydir = console.dir;
    // initialize csv
    window.CSV_GYMS = "";
    (function() {
       var origOpen = XMLHttpRequest.prototype.open;
       // add our hanldler as a listener to every XMLHttpRequest
       XMLHttpRequest.prototype.open = function() {
         this.addEventListener('load', function(xhr) {
           if(this.responseText.indexOf("gyms") > 0){
               var json = JSON.parse(this.responseText);
               var gyms = json.gyms;
               ohmylog("Received response with " + gyms.length + " gyms");
               if(gyms.length>0){
                 var csv = window.CSV_GYMS;
                 ohmylog('Gymscraping in action!!');
                 for(var j = 0; j < gyms.length; j++){
                     var gym = gyms[j];
                     // decode base64 until a max of 10 attemps
                     for(var i = 0; i < 10; i++){
                         if(gym.indexOf("gym_id") >= 0){
                           // conver text to JSON
                           ohmylog("Gym info: " + gym);
                           gym = JSON.parse(gym);
                           ohmylog("Found gym id " + gym.gym_id);
                           // append a row to the csv if not already there
                           var row = gym.gym_name + "\t" + gym.longitude + "\t"+ gym.latitude;
                           if(csv.indexOf(row) == -1){
                               csv = csv + row +"\n";
                           }
                           break;
                         }
                         // if not valid, try to base64decode it
                         gym = Base64.decode(gym);
                     }
                 }
                 window.CSV_GYMS = csv;
                 showDownloadButton();
                 ohmylog("CSV contents: " + csv);
                 ohmylog('Gymscraping ended!!');
               }
           }
         });
         origOpen.apply(this, arguments);
       };
    })();
})();

 // Code for decoding Base64. https://gist.github.com/jarus/948005
var Base64 = { characters: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" , encode: function( string ) { var characters = Base64.characters; var result = ''; var i = 0; do { var a = string.charCodeAt(i++); var b = string.charCodeAt(i++); var c = string.charCodeAt(i++); a = a ? a : 0; b = b ? b : 0; c = c ? c : 0; var b1 = ( a >> 2 ) & 0x3F; var b2 = ( ( a & 0x3 ) << 4 ) | ( ( b >> 4 ) & 0xF ); var b3 = ( ( b & 0xF ) << 2 ) | ( ( c >> 6 ) & 0x3 ); var b4 = c & 0x3F; if( ! b ) { b3 = b4 = 64; } else if( ! c ) { b4 = 64; } result += Base64.characters.charAt( b1 ) + Base64.characters.charAt( b2 ) + Base64.characters.charAt( b3 ) + Base64.characters.charAt( b4 ); } while ( i < string.length ); return result; } , decode: function( string ) { var characters = Base64.characters; var result = ''; var i = 0; do { var b1 = Base64.characters.indexOf( string.charAt(i++) ); var b2 = Base64.characters.indexOf( string.charAt(i++) ); var b3 = Base64.characters.indexOf( string.charAt(i++) ); var b4 = Base64.characters.indexOf( string.charAt(i++) ); var a = ( ( b1 & 0x3F ) << 2 ) | ( ( b2 >> 4 ) & 0x3 ); var b = ( ( b2 & 0xF ) << 4 ) | ( ( b3 >> 2 ) & 0xF ); var c = ( ( b3 & 0x3 ) << 6 ) | ( b4 & 0x3F ); result += String.fromCharCode(a) + (b?String.fromCharCode(b):'') + (c?String.fromCharCode(c):''); } while( i < string.length ); return result; } };
