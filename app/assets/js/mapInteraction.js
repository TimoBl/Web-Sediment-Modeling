var map = L.map('mapid', {
    crs: L.CRS.EPSG2056,
    preferCanvas: true // use this for adding markers
}).setView([46.859588, 7.529822], 17);

// var marker
var marker_circle = L.divIcon({
    className: 'marker_circle',
    iconSize: [6, 6], 
})

/*L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(map);*/

L.tileLayer.swiss({
    layer: 'ch.swisstopo.swissimage',
    //maxNativeZoom: 28
}).addTo(map)


var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

var drawControl = new L.Control.Draw({
    edit: {
        featureGroup: drawnItems,
        edit: true,
        remove: true
    },
    draw: {
        circle: false,
        circlemarker: false,
        marker: false,
        polyline: false,
        rectangle: false,
        polygon: {
            allowIntersection: false,
            showArea: true,
            drawError: {
                color: '#b00b00',
                timeout: 1000
            },
            shapeOptions: {
                color: '#bada55'
            }
        }
    }
});

map.addControl(drawControl);

map.on(L.Draw.Event.CREATED, function (event) {
    drawnItems.addLayer(event.layer);
});


// for rendering markers
var myRenderer = L.canvas();
show_markers(myRenderer)


function submitPolygon(link) {
    var latlngs = [];

    drawnItems.eachLayer(function (layer) {
        if (layer instanceof L.Polygon) {
            var poly = []
            for (const latlng of layer.getLatLngs()[0]){
                var l = L.CRS.EPSG2056.project(latlng);
                poly.push([l["x"], l["y"]]) // convert to LV95
            }
            latlngs.push(poly)
        }
    });

    // we should add additionnal tests here before submission!
    // maybe only allow one polygon submission -> we are either way taking the first polygon in submission
    
    var polygon = JSON.stringify(latlngs);
    $.ajax({
        type: 'POST',
        url: link,
        data: {
            'coordinates': polygon,
            'name': $("#filter-name").val(),
            'sx': parseInt($("#filter-x-resolution").val()),
            'sy': parseInt($("#filter-y-resolution").val()),
            'sz': parseInt($("#filter-z-resolution").val()),
            'oz': parseInt($("#filter-origin").val()),
            'z1': parseInt($("#filter-depth").val())
        },
        success: function(data, textStatus){
            window.location.href = data; // redirects to submission page
        }
    });
}