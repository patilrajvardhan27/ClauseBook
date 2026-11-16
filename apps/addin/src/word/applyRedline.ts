/**
 * Applies a finding's diff hunks as a real tracked change.
 *
 * Turns on change tracking, then walks the hunks in order: an "equal" hunk
 * just advances where we are in the clause, a "delete" hunk removes that
 * exact text, an "insert" hunk inserts new text at the current position.
 * Word's Range objects only stay valid within a sync batch, so this syncs
 * after every mutation and re-anchors from the clause's current end each
 * time, rather than holding one Range object across the whole walk.
 *
 * Written against the documented Word JS API surface (WordApi 1.4+ for
 * change tracking); not yet run against a live Word host, which the day-8
 * demo step in the build plan is where that first happens.
 */
import type { DiffHunk } from "@clausebook/api-client";

export async function applyRedline(
  context: Word.RequestContext,
  clauseRange: Word.Range,
  hunks: DiffHunk[],
): Promise<void> {
  context.document.changeTrackingMode = Word.ChangeTrackingMode.trackAll;
  await context.sync();

  let anchor = clauseRange.getRange(Word.RangeLocation.start);

  for (const hunk of hunks) {
    if (hunk.op === "equal") {
      anchor = await advancePastEqualText(context, anchor, hunk.text);
    } else if (hunk.op === "delete") {
      anchor = await deleteNextOccurrence(context, anchor, hunk.text);
    } else {
      anchor.insertText(hunk.text, Word.InsertLocation.before);
      await context.sync();
      anchor = anchor.getRange(Word.RangeLocation.after);
      await context.sync();
    }
  }
}

async function advancePastEqualText(context: Word.RequestContext, anchor: Word.Range, text: string): Promise<Word.Range> {
  const match = anchor.getRange(Word.RangeLocation.after).search(text.slice(0, 200), { matchCase: false }).getFirstOrNullObject();
  match.load("isNullObject");
  await context.sync();
  if (match.isNullObject) return anchor;
  return match.getRange(Word.RangeLocation.after);
}

async function deleteNextOccurrence(context: Word.RequestContext, anchor: Word.Range, text: string): Promise<Word.Range> {
  const match = anchor.getRange(Word.RangeLocation.after).search(text.slice(0, 200), { matchCase: false }).getFirstOrNullObject();
  match.load("isNullObject");
  await context.sync();
  if (match.isNullObject) return anchor;

  const afterDelete = match.getRange(Word.RangeLocation.after);
  match.delete();
  await context.sync();
  return afterDelete;
}
