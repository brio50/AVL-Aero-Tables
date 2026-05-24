// Plotly WebGL context management via IntersectionObserver.
//
// Each Plotly 3-D figure uses one WebGL context per subplot (up to 6 per
// iframe).  Chrome limits concurrent WebGL contexts to ~16 per page.  With
// several tab sets on the page, contexts accumulate as the user visits tabs
// and scrolls — older iframes (Stability, CL) get evicted and go blank.
//
// Fix: watch every iframe.plotly-iframe in the parent page.  When an iframe
// leaves the viewport (tab hidden, scrolled away), blank its src to release
// its WebGL contexts.  When it enters the viewport, restore its src so it
// reloads fresh.  Only iframes actually on-screen ever hold contexts.
//
// rootMargin "400px" gives a small preload buffer so the iframe starts
// loading before it fully enters view.

document.addEventListener("DOMContentLoaded", function () {
    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            var iframe = entry.target;
            if (entry.isIntersecting) {
                if (iframe._plotlySrc && iframe.getAttribute("src") !== iframe._plotlySrc) {
                    iframe.setAttribute("src", iframe._plotlySrc);
                }
            } else {
                if (!iframe._plotlySrc) {
                    iframe._plotlySrc = iframe.getAttribute("src");
                }
                if (iframe.getAttribute("src") !== "about:blank") {
                    iframe.setAttribute("src", "about:blank");
                }
            }
        });
    }, { rootMargin: "400px" });

    document.querySelectorAll("iframe.plotly-iframe").forEach(function (iframe) {
        if (!iframe._plotlySrc) iframe._plotlySrc = iframe.getAttribute("src");
        observer.observe(iframe);
    });
});
