function submit_Form() {
    const body = {
        "form": document.getElementById("bacteria").value
    };

    $.ajax({
        type: "POST",
        url: "/message",
        data: JSON.stringify(body),
        contentType: "application/json",
        success: function (data, status) {
            console.log(`${JSON.stringify(data)} and status is ${status}`);
            if (data.results) {
                window.location.href = "/results/" + encodeURIComponent(data.results);
            }
        }
    });
}

