// config-bootstrap.js — 启动时从 /config.json 加载 API 地址，写入 localStorage（优先级低于用户手动设置）
// N5（audit 2026-08-18）: 原为 index.html 内联 <script>, 为把 CSP script-src 去掉 'unsafe-inline'
// 而外置为 public/ 静态文件（同源 'self' 加载, 行为不变）。public/ 文件会被 Vite 原样拷贝到构建根。
(function () {
  var stored = localStorage.getItem('dp_api_config');
  if (stored) { try { var c = JSON.parse(stored); if (c.apiUrl) return; } catch (e) {} }
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/config.json', true);
  xhr.timeout = 3000;
  xhr.onload = function () {
    if (xhr.status === 200) {
      try {
        var cfg = JSON.parse(xhr.responseText);
        if (cfg.apiUrl && !cfg.apiUrl.includes('YOUR_BACKEND_URL')) {
          var prev = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
          if (!prev.apiUrl) {
            prev.apiUrl = cfg.apiUrl;
            localStorage.setItem('dp_api_config', JSON.stringify(prev));
          }
        }
      } catch (e) {}
    }
  };
  xhr.send();
})();
