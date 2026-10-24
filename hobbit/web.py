"""Page setup for the browser build (pygbag): crisp pixels and the F key for fullscreen."""

import platform     # pygbag's bridge to the page (platform.window is the JS window)

PAGE = """
(() => {
  // the 320x200 canvas is stretched by the page: keep the pixels sharp
  const style = document.createElement("style");
  style.textContent = "canvas { image-rendering: pixelated; image-rendering: crisp-edges; }";
  document.head.appendChild(style);
  // browsers only allow fullscreen on a key press, so the page handles F itself
  window.addEventListener("keydown", ev => {
    if (ev.code !== "KeyF" || ev.repeat) return;
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen().catch(() => {});
  }, true);
})();
"""


def setup():
    platform.window.eval(PAGE)
