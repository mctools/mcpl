---
weight: 99999
---

Test page

|---
| Default aligned | Left aligned | Center aligned | Right aligned
|-|:-|:-:|-:
| First body part | Second cell | Third cell | fourth cell
| Second line |foo | **strong** | baz
| Third line |quux | baz | bar
|---
| Second body
| 2 line
|===
| Footer row


|---
| **Particle state information** |
|---
| _Field_ | _Description_ | _Bytes of storage used per entry (FP = 4 or 8 bytes)_ |
|---
| PDG code       | 32 bit integer indicating particle type. | 0 or 4 |
| Position       | Vector, values in centimetres.           | 3FP |
| Direction      | Unit vector along the particle momentum. | 2FP |
| Kinetic energy | Value in MeV.                            | 1FP |
| Time           | Value in milliseconds.                   | 1FP |
| Weight         | Weight or intensity.                     | 0 or 1FP |
| Polarisation   | Vector.                                  | 0 or 3FP |
| User-flags     | 32 bit integer with custom info. | 0 or 4 |
|---

Bla: Particle state information available and uncompressed storage requirements for each entry in the data section of MCPL files.
