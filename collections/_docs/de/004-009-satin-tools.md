---
title: "Satin Werkzeuge"
permalink: /de/docs/satin-tools/
excerpt: ""
last_modified_at: 2021-10-30
toc: true
---
Unter `Erweiterungen > Ink/Stitch  > Satin Tools` befindet sich eine kleine Anzahl nützlicher Helfer, die das Arbeiten mit [Satinsäulen](/docs/stitches/satin-column/) erleichtern sollen.

**Beispiel:**
* Erzeuge einen Pfad mit dem Beziér-Kurven Werkzeug (`B`)
* Benutze "[Linie zu Satin](/de/docs/satin-tools/#linie-zu-satin)"
* Aktiviere im [Parameter Dialogfenster](/de/docs/params/#satinsäule) eine oder mehrere Unterlagen
* Führe "[Automatische Satinsäulenführung](/docs/satin-tools/#automatische-satinsäulenführung)" aus, um optimal geführte Satinsäulen zu erhalten

[![Convert Line to Satin](/assets/images/docs/en/satin-tools.svg)](/assets/images/docs/en/satin-tools.svg){: title="Download SVG File" download="satin-tools.svg" }

**Tip:** Setze [Tastenkürzel](/docs/customize/) um die einzelnen Satin-Werkzeuge schneller ausführen zu können.
{: .notice--info}

## Automatisch geführte Satinsäulen...

Dieses Werkzeug ersetzt deine Satinsäulen mit einem Set von neuen Satinsäulen in logischer Reihenfolge. Sprungstiche werden hinzugefügt, falls nötig, optional werden stattdessen Fadenschneide-Befehle eingesetzt. Um Sprungstiche zu vermeiden werden Satinsäulen getrennt und versteckte Geradstiche hinzugefügt. Die neuen Satinsäulen behalten alle Einstellungen bei, die zuvor über den Paramter-Dialog gesetzt wurden, einschließlich Unterlage, Zick-Zack-Abstand, etc.

### Funktionsweise

1. Wähle eine Satinsäule an (fertig vorbereitet mit Unterlage, etc.)
2. Führe `Erweiterungen > Ink/Stitch  > Satin Tools > Auto-Route Satin Columns...` aus
3. Aktiviere die gewünschten Optionen und klicke auf "Anwenden"

**Tip:** Standardmäßig beginnen automatisch geführte Satinsäulen links und enden rechts. Du kannst dieses Verhalten mit den Befehlen "[Start- und Enpunkt für automatisch geführte Satinsäulen](/de/docs/visual-commands/#--start--und-endposition-für-automatisch-geführte-satinsäulen)" überschreiben.
{: .notice--info }

### Optionen

* Aktiviere **Trim jump stitches** um anstelle von Sprungstichen den Faden zu trennen. Jeder Sprungstich über einem Milimeter wird getrennt. Fadenschneide-Befehle werden der SVG-Datei hinzugefügt, somit ist es auch nachträglich noch möglich sie zu modifizieren.

* Solltest du es bevorzugen die vorher gesetzte Objekt-Reihenfolge beizubehalten (das könnte der Fall sein, wenn sich die Satinsäulen überschneiden), benutze die Option **Preserve order of Satin Columns**.

## Linie zu Satin

Diese Erweiterung konvertiert einen einfachen Pfad in eine Satinsäulen. Dabei wird die Linienbreite übernommen. Nach der Konvertierung wirst du zwei "Holme" und (möglicherweise) viele Sprossen (wie bei einer Leiter). Wieviele Sprossen es gibt hängt ganz von der Form der Linie ab.

### Funktionsweise

1. Zeichne eine Beziér-Kurve (`B`)
2. Stelle die Linienbreite ein (`Ctrl+Shift+F)
2. Führe `Erweiterungen > Ink/Stitch  > Satin Tools > Linie zu Satin` aus

## Satin zu Linie

Satinsäule zu Linie konvertiert eine Satinsäule in ihre Mittellinie. Das ist besonders dann hilfreich, wenn du während des Designprozesses eine Satinsäule in einen Geradstich abändern willst. Du kannst diese Funktion auch benutzen, wenn du die Breite der Satinsäule ändern willst, aber der Parameter Zugausgleich nicht zum gewünschten Ergebnis (oder zu Überschneidungen) führt. In diesem Fall kannst du die Satinsäule in einen Geradstich ändern, um im Anschluss die Weite im "Füllung und Kontur"-Panel anzupassen. Die Funktion ["Linie zu Satin"](#linie-zu-satin) führt den Geradstich wieder in eine Satinsäule zurück. 

Das funktioniert am Besten mit Satinsäulen gleicher Breite.

![Satin to Stroke example](/assets/images/docs/en/satin_to_stroke.png)

### Funktionsweise

1. Wähle eine oder mehrere Satinsäulen aus, die in einen Geradstich umgewandelt werden sollen
2. Öffne `Erweiterungen > Ink/Stitch > Satinwerkzeuge > Satin zu Linie...`
3. Wähle, ob die ursprünglichen Satinsäulen beibehalten oder gelöscht werden sollen
4. Klicke auf "Anwenden"

## Satinsäule schneiden

Diese Option schneidet eine Satinsäule an einem vordefiniertem Punkt. Alle Parameter die der Säule zuvor zugewiesen wurden werden auf beide Teile übertragen. Auch alle Sprossen bleiben erhalten. Sollte eine der beiden Säulen keine Sprossen beinhalten, wird eine Neue hinzugefügt.

### Funktionsweise

1. Wähle eine Satinsäule an (eine Zick-Zack-Linie funktioniert hier nicht)
2. Füge über `Erweiterungen > Ink/Stitch  > Befehle > Befehle mit gewählten Objekten verknüpfen > Satin cut point` einen "Satin-Schnittstelle"-Befehl ein
3. Bewege das Symbol zur gewünschten Stelle. Der Zeiger muss genau auf die Stelle treffen, wo die Satinsäule geschnitten werden soll
4. Wähle die Satinsäule erneut an
5. Führe `Erweiterungen > Ink/Stitch  > Satin Tools > Satinsäule schneiden` aus
6. Der Satin-Schnittstelle-Befehl und sein Zeiger sind verschwunden. Wähle die Satinsäule aus: es sind jetzt zwei.

## Satinsäule umkehren

Dies ist ein kleines Werkzeug, mit dem der Stichpfad genau geplant werden kann. Bei Anwendung kehrt es eine Satinsäule, die auf der linken Seite beginnt und auf der rechten Seite endet, um. Diese wird nun auf der rechten Seite beginnen und auf der linken Seite enden.
Sonst wird nichts an der Satinsäule verändert.

![Flip Satin Columns](/assets/images/docs/en/flip-satin-column.jpg)

### Funktionsweise

* Wähle eine oder mehrere Satinsäule(n) aus
* Starte `Erweiterungen -> Ink/Stitch -> Satinsäule umkehren`

## Stroke to Live Path Effect Satin

{% include upcoming_release.html %}

Converts a stroke into a satin using a live path effect. This makes it more adaptable in width and shape as a normal satin column.

### Usage

1. Select a Stroke
2. Run `Extensions > Ink/Stitch > Tools: Satin > Stroke to Live Path Effect Satin...`
3. Set the approximate sizes that you wish your satin to be
4. Click on apply

### Update and change the pattern

Now you can change the pattern in the following ways.

* Update the path as every other path in inkscape with the node tool
* Change pattern by opening the path effects dialog (`Path > Path Effects`).
  * Make the satin wider or thinner by manipulating the `width` setting.
  * Change the pattern element, by clicking `Edit on-canvas` in the `pattern source` setting.
    
    ![edit on canvas](/assets/images/tutorials/pattern-along-path/edit.png)
* Change the pattern by running this tool again
* Convert it to a normal path (`Shift + Ctrl + C`) and refine the path manually (it will then lose the path effect functionality)
