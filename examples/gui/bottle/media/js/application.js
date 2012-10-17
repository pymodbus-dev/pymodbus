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
  parse: function(data) {
    return {
      'delimiter': data.delimiter.replace('\r', '\\r'),
      'mode': data.mode,
      'readonly': data.readonly
    }
  }
});

var DataStore = Backbone.Model.extend({
  defaults : {
    'type' : 'coils',
    'start': 0,
    'count': 100,
    'data' : {},
  },
  url: function() {
    return ['/api/v1',
      this.get('type'),
      this.get('start'),
      this.get('count')].join('/')
  },
  parse: function(data) {
    return {
      'data'  : data.data
      //'count' : _.keys(data.data).length
      //'start' : _.first(_.keys(data.data))
    };
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

var DataStoreView = Backbone.View.extend({
  template: _.template($('#py-datastore-template').html()),
  initialize: function() {
    this.model.bind('change', this.render, this);
    this.model.fetch();
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
  el: '#py-container',
  initialize: function() {
    this.device   = new DeviceView({ model: new Device() });
    this.counters = new CountersView({ model: new Counters() });
    this.identity = new IdentityView({ model: new Identity() });

    this.datastores = [
      new DataStoreView({ model: new DataStore({ type: 'coils' }) }),
      new DataStoreView({ model: new DataStore({ type: 'discretes' }) }),
      new DataStoreView({ model: new DataStore({ type: 'holdings' }) }),
      new DataStoreView({ model: new DataStore({ type: 'inputs' }) })
    ];
  },

  render: function() {
    this.$('#py-identity').html(this.identity.render().el);
    this.$('#py-counters').html(this.counters.render().el);
    this.$('#py-device').html(this.device.render().el);

    _.each(this.datastores, function(store) {
      var name = '#pane-' + store.model.get('type');
      $(name).html(store.render().el);
    });
  },
});

jQuery(function initialize($) {
  window.app = new Application();
  window.app.render();
});
