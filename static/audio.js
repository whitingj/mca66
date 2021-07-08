/* global $: false */

/* jshint -W097 */
'use strict';

function disable(elem, yes) {
  if (yes) {
    //elem.removeAttr('disabled');
  } else {
    //elem.attr('disabled', 'disabled');
  }
}

var audio = {
  state: {},
  boundEvents: false,
  desiredVolume: -1,
  zoneNames: {
    1: 'Craft',
    2: 'Kitchen',
    3: 'Patio',
    4: 'Master Bd',
    5: 'Loft',
    6: 'Laundry'
  },
  getHost: function() {
    return window.location.hostname;
  },
  updateState: function(state) {
    for (var i in state) {
      this.state[i] = state[i];
      this.state[i].name = this.zoneNames[i];
    }
    this.sync(Object.keys(state));
  },
  _getZone: function(e) {
    return e.name.split(/-/)[1];
  },
  changePower: function(event) {
    var zone = this._getZone(event.target);
    var value = event.target.value == 'on' ? 1 : 0;
    value = {power: value};
    console.log('power', value);

    $.ajax({
      url: 'http://'+this.getHost()+'/zone/'+zone+'/power',
      type: 'PUT',
      data: value 
    }).done(function(data) {
      audio.updateState(data);
    });
  },
  changeVolume: function(event) {
    var that = this;
    //only change the volume if we haven't had a change in the last 500ms
    var zone = that._getZone(event.target);
    that.disableVolume(zone);
    $.ajax({
      url: 'http://'+this.getHost()+'/zone/'+zone+'/volume',
      type: 'PUT',
      data: {volume: event.target.value}
    }).done(function(data) {
      that.enableVolume(zone);
      audio.updateState(data);
    });
  },
  changeInput: function(event) {
    console.log('input', arguments);
    var zone = this._getZone(event.target);
    $.ajax({
      url: 'http://'+this.getHost()+'/zone/'+zone+'/input',
      type: 'PUT',
      data: {input: event.target.value}
    }).done(function(data) {
      audio.updateState(data);
    });
  },
  bindEvents: function() {
    this.boundEvents = true;
    $('input[type=radio]').bind('change', this.changePower.bind(this));
    $('input[type=number]').bind('slidestop', this.changeVolume.bind(this));
    $('select').bind('change', this.changeInput.bind(this));
  },
  disableVolume: function(zoneId) {
    console.log("disable", zoneId);
    $('#volume-'+zoneId).slider('disable').slider('refresh');
  },
  enableVolume: function(zoneId) {
    console.log("enable", zoneId);
    $('#volume-'+zoneId).slider('enable').slider('refresh');
  },
  sync: function(zoneIds) {
    if (!this.boundEvents) {
      this.bindEvents();
    }
    for (var i in this.state) {
      if (zoneIds.indexOf(i) == -1) {
        continue;
      }
      var s = this.state[i];
      console.log('updating', i, s);
      if (s.power) {
        $('#zone-'+i).addClass('on');
        $('#zone-'+i).removeClass('off');
      } else {
        $('#zone-'+i).addClass('off');
        $('#zone-'+i).removeClass('on');
      }
      var enabled = s.power ? 'enable' : 'disable';
      $('#title-'+i).html(s.name);
      if (s.power) {
        $('#power-'+i+'-on').prop('checked', true).checkboxradio('refresh');
        $('#power-'+i+'-off').prop('checked', false).checkboxradio('refresh');
      } else {
        $('#power-'+i+'-on').prop('checked', false).checkboxradio('refresh');
        $('#power-'+i+'-off').prop('checked', true).checkboxradio('refresh');
      }
      $('#input-'+i)[0].selectedIndex = s.input - 1;
      $('#input-'+i).selectmenu(enabled).selectmenu('refresh');

      $('#volume-'+i).val(s.volume).slider(enabled).slider('refresh');
    }
  }
};

$.ajax({
  url: 'http://'+audio.getHost()+'/status'
}).done(function(data) {
  audio.updateState(data);
});
