document.addEventListener("DOMContentLoaded", function () {
    // Resize plotly iframes when a sphinx-design tab becomes visible.
    document.querySelectorAll('input[type="radio"][name^="sd-tab-set-"]').forEach(function (input) {
        input.addEventListener("change", function () {
            var label = input.nextElementSibling;
            var content = label && label.nextElementSibling;
            if (!content || !content.classList.contains("sd-tab-content")) return;
            requestAnimationFrame(function () {
                if (typeof Plotly === "undefined") return;
                content.querySelectorAll(".plotly-graph-div").forEach(function (div) {
                    Plotly.relayout(div, { autosize: true });
                });
            });
        });
    });

});
