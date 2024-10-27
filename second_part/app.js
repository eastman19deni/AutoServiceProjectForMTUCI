let map;
function initMap() {
    map = new ymaps.Map("yandexmap", {
        center: [55.7558, 37.6176],
        zoom: 16
    });
}
ymaps.ready(initMap);