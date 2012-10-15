//------------------------------------------------------------
// models
//------------------------------------------------------------
var Counters = Backbone.Model.extend({
  url: '/api/v1/device/counters',
  sync: function(m, m, o) {},
  parse: function(data) {
    return data.counters;
  }
});

var Identity = Backbone.Model.extend({
  url: '/api/v1/device/identity',
  sync: function(m, m, o) {},
  parse: function(data) {
    return data.identity;
  }
});

var Device = Backbone.Model.extend({
  url: '/api/v1/device',
  defaults : {
    'delimiter' :'\r',
    'mode': 'ASCII',
    'readonly': false,
  },
  sync: function(m, m, o) {},
  parse: function(data) {
    return {
      'delimiter': data.delimiter,
      'mode': data.mode,
      'readonly': data.readonly
    }
  }
});

//------------------------------------------------------------
// views
//------------------------------------------------------------
var CounterView = Backbone.View.extend({
  id: 'py-counters',
  template: _.template($('#py-table-template').html()),
  initialize() {
    this.model.bind('change', this.render, this);
  },
  render: function() {
    this.$el.html(this.template(this.model.toJSON()));
    return this;
  }
});

var IdentityView = Backbone.View.extend({
  id: 'py-identity',
  template: _.template($('#py-table-template').html()),
  initialize() {
    this.model.bind('change', this.render, this);
  },
  render: function() {
    this.$el.html(this.template(this.model.toJSON()));
    return this;
  }
});

var DeviceView = Backbone.View.extend({
  id: 'py-device',
  template: _.template($('#py-table-template').html()),
  initialize() {
    this.model.bind('change', this.render, this);
  },
  render: function() {
    this.$el.html(this.template(this.model.toJSON()));
    return this;
  }
});

//------------------------------------------------------------
// application
//------------------------------------------------------------
var Application = Backbone.View.extend({
  el: '#container',
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
