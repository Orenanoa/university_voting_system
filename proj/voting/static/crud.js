/* Shared helpers: talk to the Django JSON API and render tables with Edit / Delete. */
function getCookie(name) {
  var m = document.cookie.match("(?:^|; )" + name + "=([^;]*)");
  return m ? decodeURIComponent(m[1]) : "";
}

async function api(url, method, body) {
  var opt = {
    method: method || "GET",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") }
  };
  if (body !== undefined) opt.body = JSON.stringify(body);
  var r = await fetch(url, opt);
  var data = null;
  try { data = await r.json(); } catch (e) {}
  if (r.status === 401 && url.indexOf("/api/login/") < 0) {
    window.location.href = "/login.html";
    throw new Error("Please log in.");
  }
  if (!r.ok) throw new Error((data && data.error) || "Request failed (" + r.status + ")");
  return data;
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}

function say(text, ok) {
  var m = document.getElementById("msg");
  if (!m) return;
  m.style.color = ok ? "#14532d" : "#b00020";
  m.textContent = text || "";
}

function fillSelect(id, items) {
  var sel = document.getElementById(id);
  sel.innerHTML = '<option value="">-- Select --</option>' +
    items.map(function (i) { return '<option value="' + esc(i.id) + '">' + esc(i.label) + "</option>"; }).join("");
}

async function doLogout(e) {
  if (e) e.preventDefault();
  try { await api("/api/logout/", "POST"); } catch (x) {}
  sessionStorage.removeItem("voterName");
  window.location.href = "/login.html";
  return false;
}

/*
 cfg = {
   resource: "student",            // /api/<resource>/
   label: "Student",
   ids:  ["studentid", ...],       // form element ids
   keys: ["student_id", ...],      // JSON keys (same order as ids)
   extra: { election_id: "id" },   // read-only form boxes -> row key
   cols: [function(row){...}],     // table cells
   selects: [{id, resource, label: function(item){...}}],
   saveBtn: "saveBtn", saveText: "Register",
   required: "Please fill in all the fields.",
   after: function(rows){}
 }
*/
function Crud(cfg) {
  var rows = [], editing = null, self = this;
  var $ = function (i) { return document.getElementById(i); };

  function draw() {
    $("rows").innerHTML = rows.map(function (r) {
      return "<tr>" + cfg.cols.map(function (c) { return "<td>" + esc(c(r)) + "</td>"; }).join("") +
        '<td><button type="button" class="blue" onclick="crud.edit(' + r.id + ')">Edit</button>' +
        '<button type="button" class="red" onclick="crud.remove(' + r.id + ')">Delete</button></td></tr>';
    }).join("") || '<tr><td colspan="' + (cfg.cols.length + 1) + '">Nothing here yet.</td></tr>';
  }

  self.rows = function () { return rows; };
  self.editingRow = function () {
    return rows.filter(function (r) { return r.id === editing; })[0] || null;
  };

  self.load = async function () {
    try {
      rows = await api("/api/" + cfg.resource + "/");
      draw();
      if (cfg.after) cfg.after(rows);
    } catch (e) { say(e.message); }
  };

  self.clear = function (keepMessage) {
    $("f").reset();
    editing = null;
    if (cfg.saveBtn) $(cfg.saveBtn).textContent = cfg.saveText;
    if (!keepMessage) say("");
  };

  self.edit = function (id) {
    var r = rows.filter(function (x) { return x.id === id; })[0];
    if (!r) return;
    editing = id;
    cfg.ids.forEach(function (el, i) { $(el).value = r[cfg.keys[i]]; });
    Object.keys(cfg.extra || {}).forEach(function (el) { $(el).value = r[cfg.extra[el]]; });
    if (cfg.saveBtn) $(cfg.saveBtn).textContent = "Update " + cfg.label;
    say("Editing " + cfg.label.toLowerCase() + " #" + id + ". Change the fields and press Update.", true);
    window.scrollTo(0, 0);
  };

  // returns true when saved
  self.save = async function () {
    var body = {};
    for (var i = 0; i < cfg.ids.length; i++) {
      var box = $(cfg.ids[i]);
      if (box.value.trim() === "") {
        say(cfg.required || "Please fill in all the fields.");
        box.focus();
        return false;
      }
      body[cfg.keys[i]] = box.value.trim();
    }
    try {
      if (editing) await api("/api/" + cfg.resource + "/" + editing + "/", "PUT", body);
      else await api("/api/" + cfg.resource + "/", "POST", body);
      self.clear(true);
      say(cfg.label + " saved successfully.", true);
      await self.load();
      return true;
    } catch (e) { say(e.message); return false; }
  };

  self.remove = async function (id) {
    if (!confirm("Delete this " + cfg.label.toLowerCase() + "? Related records may be deleted too.")) return;
    try {
      await api("/api/" + cfg.resource + "/" + id + "/", "DELETE");
      if (editing === id) self.clear();
      say(cfg.label + " deleted.", true);
      await self.load();
    } catch (e) { say(e.message); }
  };

  self.init = async function () {
    try {
      for (var s of (cfg.selects || [])) {
        var items = await api("/api/" + s.resource + "/");
        fillSelect(s.id, items.map(function (i) { return { id: i.id, label: s.label(i) }; }));
      }
    } catch (e) { say(e.message); }
    await self.load();
  };
}
