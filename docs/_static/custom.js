// Plotly resize on visibility change.
//
// Plotly figures inside sphinx-design tabs start hidden, so they render at
// 0x0.  An IntersectionObserver fires when a .plotly-graph-div enters the
// viewport (tab click, scroll-back, initial load) and dispatches a window
// resize event.  All figures are created with responsive:true, so Plotly's
// built-in resize handler re-measures the container and redraws the figure.

document.addEventListener("DOMContentLoaded", function () {
    if (typeof Plotly === "undefined") return;

    var observer = new IntersectionObserver(
        function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                window.dispatchEvent(new Event("resize"));
            });
        },
        { threshold: 0.01 }
    );

    document.querySelectorAll(".plotly-graph-div").forEach(function (gd) {
        observer.observe(gd);
    });
});
