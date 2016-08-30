from .core import main

# It is important to keep the __main__ module away from our global state,
# so we are actually running the loop here.
main()
