"""Fixed verification inputs extracted from the published manuscript.

The 120-state digest covers the literal Appendix I listing, including its
header and final newline, encoded as UTF-8 with LF line endings. It was
extracted independently of the compiler. The 121-state digest covers the
recovered archive baseline/RH_121.tm in the same encoding. The 119-state
digest covers RH_119.tm, including its comment header and final newline.
The manuscript digest identifies the uploaded rhtm(2).tex used for extraction;
no manuscript download is needed to run.
"""

MANUSCRIPT_SHA256 = "d9059de4dfb96a8809cceddc35e024582581654bd68c17203d9929bda28cb179"
BASELINE_121_SHA256 = "212084bf23735b4d8ea4f1763812787a1bc48a002a4dccb322541a3bbd5ea37a"
PUBLISHED_120_SHA256 = "b4b0f07607fc92dae6940f6e6c2d184fec3c13bbfc8cd00a0253321be6009db5"
PUBLISHED_119_SHA256 = "d138ee6bd2aa50acfe1da4c5399783a7942c510c766c46fa4ab920ec92dc60ab"
