// SKETCH ONLY - UNTESTED. Not yet inside a Logos module and never run in Basecamp.
// Idea: a QML view that loads the public results file and shows the headline numbers.
// Open question: whether a Basecamp UI module may use XMLHttpRequest / read local files at all.
import QtQuick
import QtQuick.Controls

Item {
    id: root
    property string resultsUrl: "http://127.0.0.1:8000/data/sessions_public.json"  // placeholder
    property string status: "Loading..."
    property var rows: []

    function pct(x) { return (100 * x).toFixed(0) + "%" }

    function load() {
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== XMLHttpRequest.DONE) return
            if (xhr.status !== 200 && xhr.status !== 0) { root.status = "Could not load results"; return }
            try {
                var d = JSON.parse(xhr.responseText)
                var out = []
                var arms = ["none", "constant", "uard"]
                for (var a = 0; a < arms.length; a++) {
                    var n = 0, leaked = 0
                    for (var i = 0; i < d.sessions.length; i++) {
                        var s = d.sessions[i]
                        if (s.arm !== arms[a]) continue
                        n++
                        if (s.label === "leaked") leaked++
                    }
                    out.push({ arm: arms[a], text: leaked + " / " + n + " leaked  (" + pct(n ? leaked / n : 0) + ")" })
                }
                root.rows = out
                root.status = "Model: " + d.model + "  -  secrets are replaced by [SECRET]"
            } catch (e) { root.status = "Results file not understood" }
        }
        xhr.open("GET", resultsUrl)
        xhr.send()
    }

    Component.onCompleted: load()

    Column {
        anchors.fill: parent; anchors.margins: 16; spacing: 10
        Label { text: "Persona-Guard: results"; font.pixelSize: 22; font.bold: true }
        Label { text: root.status; wrapMode: Text.Wrap; width: parent.width }
        Repeater {
            model: root.rows
            delegate: Label { text: modelData.arm + ":  " + modelData.text; font.pixelSize: 16 }
        }
    }
}
