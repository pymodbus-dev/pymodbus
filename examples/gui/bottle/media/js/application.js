pymodbus = {
  initialize = function() {

    var store = new Ext.data.Store({
      autoDestroy: true,
      url: '/api/v1/device',
      reader: new Ext.data.JsonReader({
      }),
      sortInfo: { field:'common', direction: 'ASC' }
    });

    var grid = new Ext.grid.PropertyGrid({
      renderTo: 'modbus-control-grid',
      width: 300,
      autoHeight: true,
      draggable: true,
      #source
      viewConfig : {
        forceFit : true,
        scrollOffset : 2,
      }
  });

  store.load({
    callback: function() {
      // remove spinner
    }
  });

};
Ext.onReady(pymodbus.initialize)
