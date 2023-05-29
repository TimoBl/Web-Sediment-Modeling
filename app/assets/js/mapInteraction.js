var map = L.map('mapid').setView([46.859588, 7.529822], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(map);

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


function submitPolygon(link) {
    var latlngs = [];
    drawnItems.eachLayer(function (layer) {
        if (layer instanceof L.Polygon) {
            latlngs.push(layer.getLatLngs()[0]);
        }
    });
    var polygon = JSON.stringify(latlngs);
    console.log(polygon);
    $.ajax({
        type: 'POST',
        url: link,
        data: {'coordinates': polygon},
        success: function(data, textStatus){
            window.location = data; // redirects to submission page
        }
    });

}