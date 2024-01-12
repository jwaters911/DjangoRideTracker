let activityId;
document.addEventListener('DOMContentLoaded', function () {
    // Check if csrfToken is defined
    if (typeof csrfToken === 'undefined') {
        console.error('CSRF token is not defined. Check if it is set correctly in your template.');
        return;
    }

    if (typeof activity_id === 'undefined') {
        console.error('Activity ID is not defined. Check if it is set correctly in your template.');
        return;
    }
    mapboxgl.accessToken = 'pk.eyJ1IjoiandhdGVyczkxMSIsImEiOiJjbG45ZXZ3a3kwNWF6MnVsbW1oeTA5MTZxIn0.YrMX72gd7B5se8TXluSWzQ';

    const map = new mapboxgl.Map({
        container: 'map', // container ID
        style: 'mapbox://styles/mapbox/satellite-streets-v12', // style URL
        center: [-111.87744, 40.77912], // starting position [lng, lat]
        zoom: 7, // starting zoom
        pitch: 30,
        bearing: 0,
    });

    map.on('load', () => {
        // Check that coordinates are defined and not empty
        if (coordinates && coordinates.length > 0) {
            const bounds = coordinates.reduce(function (bounds, coord) {
                return bounds.extend(coord);
            }, new mapboxgl.LngLatBounds(coordinates[0], coordinates[0]));

            map.fitBounds(bounds, { padding: 20 });

            map.addSource('route', {
                'type': 'geojson',
                'data': {
                    'type': 'Feature',
                    'properties': {},
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coordinates
                    }
                }
            });

            map.addLayer({
                'id': 'route',
                'type': 'line',
                'source': 'route',
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': '#1AA7EC',
                    'line-width': 4
                }
            });
        } else {
            console.error('Invalid or missing coordinates.');
        }
    });

    map.addControl(new mapboxgl.NavigationControl());

});


