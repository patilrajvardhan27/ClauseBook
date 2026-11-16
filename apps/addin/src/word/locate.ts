/**
 * Finds a finding's clause in the open document and returns a Range
 * covering it. body.search() caps a query at 255 characters, so this
 * searches the first 200 characters of the segment text, then walks
 * paragraph by paragraph from that hit to cover the full segment length.
 */
export async function locateSegment(context: Word.RequestContext, segmentText: string): Promise<Word.Range | null> {
  const searchText = segmentText.slice(0, 200);
  const results = context.document.body.search(searchText, { matchCase: false, matchWholeWord: false });
  results.load("items");
  await context.sync();

  if (results.items.length === 0) return null;

  const start = results.items[0];
  return expandToSegmentLength(context, start, segmentText.length);
}

async function expandToSegmentLength(
  context: Word.RequestContext,
  start: Word.Range,
  totalLength: number,
): Promise<Word.Range> {
  // Office.js has no "expand by character count" primitive, so this grows
  // the range one paragraph at a time via Paragraph.getNext() (WordApi 1.3+)
  // until it covers at least the segment's length or runs out of paragraphs.
  let range = start;
  let currentParagraph = range.paragraphs.getLast();
  let guard = 0;

  while (guard < 50) {
    range.load("text");
    await context.sync();
    if (range.text.length >= totalLength) break;

    const nextParagraph = currentParagraph.getNextOrNullObject();
    nextParagraph.load("isNullObject");
    await context.sync();
    if (nextParagraph.isNullObject) break;

    range = range.expandTo(nextParagraph.getRange("Whole"));
    currentParagraph = nextParagraph;
    guard += 1;
  }
  return range;
}
