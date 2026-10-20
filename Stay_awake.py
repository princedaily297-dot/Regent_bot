import os
import staypresent

staypresent.run(
    "regent.py",
    port=int(os.environ.get("PORT", 8080))
)
