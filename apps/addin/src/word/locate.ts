// Finds a finding's clause in the open document, searching the first 200 characters then expanding.
export async function locateSegment(context: Word.RequestContext, segmentText: string): Promise<Word.Range | null> {
  const searchText = segmentText.slice(0, 200);
  const results = context.document.body.search(searchText, { matchCase: false, matchWholeWord: false });
  results.load("items");
  await context.sync();

  if (results.items.length === 0) return null;

  const start = results.items[0];
  return expandToSegmentLength(context, start, segmentText.length);
}

// Grows a range one paragraph at a time until it covers the segment's full length.
async function expandToSegmentLength(
  context: Word.RequestContext,
  start: Word.Range,
  totalLength: number,
): Promise<Word.Range> {
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
