# Logos integration

## Status (honest)
- DONE: `data/sessions_public.json` (secrets removed) was uploaded to **Logos Storage** with the File Sharing module (`hackyguru/logos-filesharing`, `filesharing_ui` v0.1.1) in Logos Basecamp 0.3.2.
- CID: `zDvZRwzm8hn5aL39xvWyrT3ViFv37ChCR1tXYa77PzmXpNgrRsQ2`
- NOT YET VERIFIED: downloading the file back from a second node by this CID.
- NOT DONE: no Persona-Guard module was written for Basecamp. Everything below this line is a plan and an untested sketch.

## Why this exists
Persona-Guard needs a GPU and PyTorch hooks, so the model and guard cannot run inside a Logos module.
The planned Logos pieces are small and separate from that:

1. **Logos Storage (planned first).** Publish `data/sessions_public.json` (secrets replaced by `[SECRET]`,
   made with `recorder/sanitize.py`) and share its CID, so anyone can fetch the same results and replay them.
   Storage returns a CID on upload; downloading needs the CID and a peer address (SPR).
2. **A `ui-qml` module (planned second).** A QML-only Basecamp module that shows the headline results.
   Start from the official template:
   `nix flake init -t github:logos-co/logos-module-builder#ui-qml`
   then use `Results.qml` here as the starting view.
3. **Calling a live guard service (unknown).** Whether a Basecamp UI module may call a local HTTP service is
   not confirmed in the docs I read. To be asked of a Logos mentor before any claim is made.

## What is NOT claimed
- The model does not run on Logos. The live demo runs on a Colab GPU.
- No Logos module has been built, packaged (`nix build .#lgx`) or run in Basecamp yet.

## Next steps, in order
1. Ask a mentor which Logos piece counts for the tracks.
2. (done, see top) Upload to Logos Storage; next: fetch it back by CID from a second node and note the result here.
3. Build the `ui-qml` template in Basecamp standalone mode (`--module`); replace the template view with `Results.qml`.
