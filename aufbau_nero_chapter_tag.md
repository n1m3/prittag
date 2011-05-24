Nero Chapter Format
===================

Im udta (Userdata) Atom befindet sich das chpl (Chapterlist) Atom,
dass folgendermaßen aufgebaut ist:
Die Zahlen sind jeweils 32 bit unsigned integers (unsigned long long).
> [Reservierter Bereich (gesetzt auf 1)][Anzahl der Kapitel][Startposition des ersten Kapitels in 100 Nanosekunden Einheiten][Länge des Namens des ersten Kapitels][Name des Kaptitels (string)][Startposition des zweiten Kapitels]...

