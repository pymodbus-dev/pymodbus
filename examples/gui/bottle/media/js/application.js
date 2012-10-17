//------------------------------------------------------------
// models
//------------------------------------------------------------
var Counters = Backbone.Model.extend({
  url: function() {
    return '/api/v1/device/counters';
  },
  parse: function(data) {
    return data.counters;
  }
});

var Identity = Backbone.Model.extend({
  url: function() {
    return '/api/v1/device/identity';
  },
  parse: function(data) {
    return data.identity;
  }
});

var Device = Backbone.Model.extend({
  url: function() {
    return '/api/v1/device';
  },
  defaults : {
    'delimiter' :'\\r',
    'mode': 'ASCII',
    'readonly': false,
  },
  parse: function(data) {
    return {
      'delimiter': data.delimiter.replace('\r', '\\r'),
      'mode': data.mode,
      'readonly': data.readonly
    }
  }
});

//------------------------------------------------------------
// views
//------------------------------------------------------------
var CountersView = Backbone.View.extend({
  template: _.template($('#py-table-template').html()),
  initialize: function() {
    this.model.bind('change', this.render, this);
    this.model.fetch();
  },
  render: function() {
    this.$el.html(this.template({'settings' : this.model.toJSON() }))
        .prepend("<h2>Device Counters</h2>");
    return this;
  }
});

var IdentityView = Backbone.View.extend({
  template: _.template($('#py-table-template').html()),
  initialize: function() {
    this.model.bind('change', this.render, this);
    this.model.fetch();
  },
  render: function() {
    this.$el.html(this.template({'settings' : this.model.toJSON() }))
        .prepend("<h2>Device Identity</h2>");
    return this;
  }
});

var DeviceView = Backbone.View.extend({
  template: _.template($('#py-table-template').html()),
  initialize: function() {
    this.model.bind('change', this.render, this);
    this.model.fetch();
  },
  render: function() {
    this.$el.html(this.template({'settings' : this.model.toJSON() }))
        .prepend("<h2>Device Settings</h2>");
    return this;
  }
});

//------------------------------------------------------------
// application
//------------------------------------------------------------
var Application = Backbone.View.extend({
  el: '#py-container',
  initialize: function() {
    this.device   = new DeviceView({ model: new Device() });
    this.counters = new CountersView({ model: new Counters() });
    this.identity = new IdentityView({ model: new Identity() });
  },

  render: function() {
    this.$('#py-identity').html(this.identity.render().el);
    this.$('#py-counters').html(this.counters.render().el);
    this.$('#py-device').html(this.device.render().el);
  },
});

jQuery(function initialize($) {
  window.app = new Application();
  window.app.render();
});
