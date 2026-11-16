// Data sources, attributions and the non-affiliation notice, per the
// plan's rule that CC BY 4.0 data requires attribution on screen.
export default function AboutPage() {
  return (
    <section>
      <h1>About</h1>
      <p>
        Clausebook is an independent portfolio project. It is not affiliated with or
        endorsed by any commercial contract-review product.
      </p>
      <h2>Data sources</h2>
      <ul>
        <li>
          <strong>CUAD v1</strong> &mdash; 510 commercial contracts, lawyer-labeled spans across 41
          clause categories. Atticus Project, CC BY 4.0. Used for segmentation and classification
          training data, the precedent corpus, and market statistics.
        </li>
        <li>
          <strong>ACORD</strong> &mdash; expert-rated query/clause pairs. CC BY 4.0. Used to evaluate
          retrieval quality (NDCG@k).
        </li>
      </ul>
      <h2>Sample playbooks</h2>
      <p>
        Playbooks labeled "sample" in this app are not any real firm's guidance. They were written
        from public drafting commentary as a stand-in so the product has something realistic to
        run against.
      </p>
    </section>
  );
}
