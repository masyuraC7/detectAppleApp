$(document).ready(function () {
    stopCamera()
    let text = ""
    let downloadImgText = ""

    $("#btnDownloadConnect").click(function (e) {
        e.preventDefault();
        $("#formDownloadPred").submit();
    })

    function imagePathController(item, index) {
        downloadImgText += "<input name='img_results[]' type='hidden' value='" + item + "'>"
        text += "<div class='col-md-6'><div class='img-container text-center'><img class='img-fluid' style='max-height: 400px;'src='" + item + "' alt='Results" + index + "'></div></div>";
    }

    function cloneSuccessAlert() {
        let cloneAlert = document.getElementById('alertSuccess').cloneNode(true);
        cloneAlert.id = "alertSuccessClone";
        document.getElementById('alertNotify').appendChild(cloneAlert);
    }

    $("#formImgPred").submit(function (e) {
        e.preventDefault();
        if (text != "") {
            text = ""
            $("#btnPredResults").addClass("hidden");
        }

        var urlPred = $("#formImgPred").attr("action")

        $.ajax({
            url: urlPred,
            type: "POST",
            data: new FormData(this),
            cache: false,
            processData: false,
            contentType: false,
            success: function (data) {
                if (data['success'] == true) {
                    var domModal = document.getElementById('modalBodyImgPred');
                    var images = data['img_results']
                    images.forEach(imagePathController);
                    // Apple Counting
                    text += "<div class='col-md-6'><div class='ml-2'><p>Jumlah Gambar: " + data['n_images'] + "</p><p>Jumlah Fresh Apple: " + data['fa_apple'] + "</p><p>Jumlah Stale Apple: " + data['sa_apple'] + "</p><p>Total Apple: " + data['n_apple'] + "</p> <form id='formDownloadPred' action='{{ url_for('predict_download') }}' method='post'>" + downloadImgText + "<button class='btn btn-success' type='submit'>Download Prediction Results</button></form></div></div>"
                    // Write text to modal
                    domModal.innerHTML = text;
                    $("#btnImgSubmit").addClass("hidden");
                    $("#btnPredResults").removeClass("hidden")
                    $("#imagesInput").attr("disabled", true);
                    cloneSuccessAlert()
                    $('#alertSuccessClone').addClass("show")
                } else {
                    alert(data['error']);
                }
            },
            error: function (data) {
                alert("Something Wrong!" + data);
            }
        });
    });

    $('#btnResetImgPred').click(function (e) {
        text = ""
        downloadImgText = ""
        $("#btnPredResults").addClass("hidden");
        $("#btnImgSubmit").removeClass("hidden");
        $("#imagesInput").attr("disabled", false);
        $("#alertSuccessClone").alert('close');
    });

    $('#myModal').on('shown.bs.modal', function () {
        $('#myInput').focus()
    })

    // realtime function
    $('#btnStartCamera').click(function () {
        startCamera();
    })

    $('#btnStopCamera').click(function () {
        stopCamera();
    })

    function startCamera() {
        fetch('/start_camera', { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    document.getElementById('video-feed').src = '/video_feed';
                } else {
                    alert('Failed to start camera.');
                }
            });
    }

    function stopCamera() {
        fetch('/stop_camera', { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    $('#videoLiveFeed').empty();
                    let htmlLiveFeed = document.getElementById('video-feed1').cloneNode(true);
                    htmlLiveFeed.id = "video-feed";
                    document.getElementById('videoLiveFeed').appendChild(htmlLiveFeed);
                    $('#video-feed').removeClass('hidden');
                } else {
                    alert('Failed to stop camera.');
                }
            });
    }
});