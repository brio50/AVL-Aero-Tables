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

    // Sync plotly iframe theme with sphinx-book-theme dark/light toggle.
    function broadcastTheme(theme) {
        document.querySelectorAll("iframe.plotly-iframe").forEach(function (iframe) {
            try {
                iframe.contentWindow.postMessage({ type: "set-theme", theme: theme }, "*");
            } catch (e) {}
        });
    }

    var observer = new MutationObserver(function () {
        broadcastTheme(document.documentElement.dataset.theme || "light");
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
});
