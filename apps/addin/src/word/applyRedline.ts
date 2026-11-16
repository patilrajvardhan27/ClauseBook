// Applies a finding's diff hunks as a real tracked change, walking equal/delete/insert in order.
// Not yet run against a live Word host; needs WordApi 1.4+ for change tracking.
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

// Moves the anchor past the next occurrence of unchanged text.
async function advancePastEqualText(context: Word.RequestContext, anchor: Word.Range, text: string): Promise<Word.Range> {
  const match = anchor.getRange(Word.RangeLocation.after).search(text.slice(0, 200), { matchCase: false }).getFirstOrNullObject();
  match.load("isNullObject");
  await context.sync();
  if (match.isNullObject) return anchor;
  return match.getRange(Word.RangeLocation.after);
}

// Finds and deletes the next occurrence of the given text, returning the range after it.
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
