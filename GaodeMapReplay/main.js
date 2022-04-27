
// url: http://127.0.0.1:5500/index.html?infos=data/%E5%A6%99%E5%B3%B0%E5%B1%B1-20220423/infos.json
function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) { return pair[1]; }
    }
    return (false);
}

function loadJson(path) {
    var request = new XMLHttpRequest();
    request.open("GET", path, false);
    request.send(null);
    return JSON.parse(request.responseText);
}

var infos = loadJson(getQueryVariable("infos"));

var app = new Vue({
    el: "#app",
    data: {
        map: null,
        marker: null,
        assetsMarkers: [],
        infos: infos,
        lineArray: [],
        passedPolyline: null,
        showImage: 0,
        showImagePath: "",
        markerStartIndex: 0,
        markerSpeed: 800,
    },
    methods: {
        convertGps: function () {
            var coords = this.infos["gx_coords"];
            var that = this;
            //convert to gaode coordinates
            AMap.convertFrom(coords, 'gps', function (status, result) {
                if (result.info === 'ok') {
                    that.lineArray = result.locations; // Array.<LngLat>
                }
            });
        },

        initMap: function () {
            console.log("this.lineArray.length: ", this.lineArray.length)
            const that = this;

            //1. create map
            this.map = new AMap.Map('container', {
                resizeEnable: false,
                center: this.infos["description"]["center"],
                layers: [
                    new AMap.TileLayer(),
                    new AMap.TileLayer.Satellite(),
                    new AMap.TileLayer.RoadNet()
                ],
            });

            var polyline = new AMap.Polyline({
                path: this.lineArray,
                strokeColor: "#3366FF",
                strokeWeight: 5,
                strokeStyle: "solid",
            });
            this.map.add(polyline);

            this.passedPolyline = new AMap.Polyline({
                map: this.map,
                strokeColor: "#AF5",
                strokeWeight: 5,
                strokeStyle: "solid"
            });

            this.marker = new AMap.Marker({
                position: this.lineArray[0],
                icon: "data/icons/IconStyle.png",
                offset: new AMap.Pixel(-28, -23),
                autoRotation: true,
                angle: -90,
                map: this.map
            });

            this.marker.on("moving", function (e) {
                var passedPath = that.lineArray.slice(0, that.markerStartIndex + e.passedPath.length);
                that.passedPolyline.setPath(passedPath);
                for (var i = 1; i < that.assetsMarkers.length - 1; i++) {
                    if ((passedPath.length == that.assetsMarkers[i].indexInArray) &&
                        (that.assetsMarkers[i].visited == false)
                    ) {
                        console.log("路过了一些marker", passedPath.length, that.assetsMarkers[i].indexInArray)
                        that.assetsMarkers[i].visited = true
                        that.assetsMarkers[i].emit("click", { target: that.assetsMarkers[i] })
                    }
                }
                if (passedPath.length == that.lineArray.length) {
                    that.marker.stopMove();
                    that.marker.hide();
                }
            });

            // 2.create more markers
            for (var i = 0; i < this.infos["assets"].length; i++) {
                var asset = this.infos["assets"][i];
                var marker = new AMap.Marker({
                    position: this.lineArray[asset["index"]],
                    icon: asset["icon_path"],
                    offset: new AMap.Pixel(-asset["icon_size"][0] / 2, -asset["icon_size"][1]),
                    map: this.map
                });

                marker.index = i   //记录是第几个mark， 知道点击了那个？
                marker.indexInArray = asset["index"]   //记录是lineArray中的位置
                marker.visited = false   //是否访问过

                marker.on('click', function (e) {
                    const asset = that.infos["assets"][e.target.index]
                    that.showImage = asset["type"] == "image" ? 1 : 2;
                    that.marker.stopMove();

                    that.showImagePath = asset["path"];
                    console.log(that.showImage, that.showImagePath);

                    doc = document.getElementById("container")
                    doc.style.opacity = 0.5;
                    that.markerStartIndex = asset["index"]
                    that.markerSpeed = 800 * asset["speed"]

                    if (asset["type"] == "image" && asset["path"] != "") {
                        setTimeout(() => {
                            doc.style.opacity = 1;
                            that.showImage = 0;
                            console.log("hide", asset["type"], that.showImagePath);
                            that.marker.moveAlong(that.lineArray.slice(that.markerStartIndex), that.markerSpeed);
                        }, 2500);
                    }
                });
                this.assetsMarkers.push(marker);
            }

            this.map.on("rightclick", this.startAnimation);
            this.map.setFitView();
        },

        videoEnded: function () {
            doc = document.getElementById("container")
            doc.style.opacity = 1;
            this.showImage = 0;
            console.log("hide video", this.showImagePath);
            this.marker.moveAlong(this.lineArray.slice(this.markerStartIndex), this.markerSpeed);
        },

        startAnimation: function () {
            this.marker.moveAlong(this.lineArray.slice(this.markerStartIndex), this.markerSpeed);
        }
    },

    mounted: function () {
        console.log("DOM加载完成");
        this.convertGps();
        setTimeout(this.initMap, 1000);
    }
})