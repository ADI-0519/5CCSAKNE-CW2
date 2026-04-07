# CQ Coverage Table

This table records how each competency question maps to the ontology and whether the current pipeline can support it.

Support legend:

- `Supported`: answerable from the current pipeline without new modelling work.
- `Partial`: answerable only with heuristic completion or weak extraction; usable but noisy.
- `Blocked`: the ontology term exists, but the current pipeline does not populate the required data yet.

The support assessment below refers to the current implementation, including the enrichment step in [complete_kg.py](/home/kasim/5CCSAKNE-CW2/src/complete_kg.py).

| CQ | Main classes | Main properties | Current support | Missing data or pipeline feature | Difficulty |
| --- | --- | --- | --- | --- | --- |
| `CQ01` | `news:NewsArticle`, `news:Journalist`, `news:Topic` | `news:hasAuthor`, `news:hasSection`, `news:hasTopic`, `news:publishedDate` | `Supported` | Better topic normalization would improve precision. | `Easy` |
| `CQ02` | `news:NewsArticle`, `news:NewsOrganisation` | `news:publishedBy`, `news:hasSection`, `news:publishedDate` | `Supported` | None beyond routine data cleaning. | `Easy` |
| `CQ03` | `news:NewsArticle`, `schema:Person` | `news:mentionsPerson`, `news:publishedDate` | `Supported` | Person disambiguation is still weak. | `Easy` |
| `CQ04` | `news:NewsArticle`, `news:PoliticalParty`, `news:Topic` | `news:mentionsOrganisation`, `news:hasTopic`, `news:publishedDate` | `Blocked` | Organisation mentions are not yet classified as `news:PoliticalParty`. | `Hard` |
| `CQ05` | `news:NewsArticle`, `news:GovernmentBody`, `news:Topic` | `news:mentionsOrganisation`, `news:hasTopic`, `news:publishedDate` | `Blocked` | Organisation mentions are not yet classified as `news:GovernmentBody`. | `Hard` |
| `CQ06` | `news:OpinionArticle`, `news:Sentiment`, `news:NewsArticle` | `news:hasSentiment`, `news:publishedDate` | `Partial` | Sentiment and opinion labels currently come from heuristic completion, not validated extraction. | `Medium` |
| `CQ07` | `news:NewsArticle`, `news:Topic` | `news:hasTopic`, `news:hasSection`, `news:publishedDate` | `Supported` | Topic labels are flat and not yet hierarchically normalized. | `Easy` |
| `CQ08` | `news:NewsArticle` | `news:publishedDate`, `news:hasUpdateTimestamp`, `news:articleURL` | `Supported` | None. | `Easy` |
| `CQ09` | `news:NewsArticle`, `news:OpinionArticle` | `news:wordCount`, `news:hasSection`, `news:publishedDate` | `Partial` | Opinion classification is still hint-based and heuristic. | `Medium` |
| `CQ10` | `news:NewsArticle`, `news:Topic` | `news:hasFollowUp`, `news:hasTopic`, `news:publishedDate` | `Partial` | Follow-up links are heuristic and not yet evidence-backed. | `Medium` |
| `CQ11` | `news:Journalist`, `news:NewsOrganisation`, `news:NewsArticle`, `news:Topic` | `news:worksFor`, `news:hasAuthor`, `news:hasTopic`, `news:publishedDate` | `Blocked` | `news:worksFor` links are modelled but not populated. | `Hard` |
| `CQ12` | `news:BreakingNewsArticle`, `news:NewsArticle` | `news:hasSection`, `news:publishedDate` | `Partial` | Breaking-news classification currently relies on simple hints and keyword rules. | `Medium` |
| `CQ13` | `news:NewsArticle`, `news:Location`, `news:Topic` | `news:mentionsLocation`, `news:hasTopic`, `news:publishedDate` | `Partial` | Location extraction is regex-based and policy-topic matching is still approximate. | `Medium` |
| `CQ14` | `news:NewsArticle`, `news:Journalist` | `news:hasAuthor`, `news:publishedDate`, `news:hasUpdateTimestamp` | `Supported` | None. | `Easy` |
| `CQ15` | `news:NewsArticle`, `schema:Person`, `news:Organisation` | `news:mentionsPerson`, `news:mentionsOrganisation`, `news:publishedDate` | `Supported` | Better entity grounding would improve result quality. | `Easy` |
| `CQ16` | `news:NewsArticle`, `news:NewsOrganisation`, `news:Topic` | `news:publishedBy`, `news:hasTopic`, `news:publishedDate` | `Supported` | Cross-source breadth is limited when NewsAPI cannot supply the fixed window. | `Easy` |
| `CQ17` | `news:NewsArticle`, `schema:Person`, `news:Organisation` | `news:mentionsPerson`, `news:mentionsOrganisation`, `news:publishedDate` | `Supported` | Co-mentions are supported, but entity disambiguation is still weak. | `Medium` |
| `CQ18` | `news:PoliticalEvent`, `news:Location`, `news:NewsArticle` | `news:eventLocation`, `news:eventDate`, `news:coversEvent` | `Blocked` | Event extraction and event instance creation are not yet implemented. | `Hard` |
| `CQ19` | `news:PoliticalEvent`, `news:EconomicEvent`, `news:NewsOrganisation`, `news:NewsArticle` | `news:coversEvent`, `news:publishedBy`, `news:publishedDate` | `Blocked` | No populated event layer exists yet. | `Hard` |
| `CQ20` | `news:Politician`, `news:PoliticalParty`, `news:NewsArticle` | `news:mentionsPerson`, `news:mentionsOrganisation`, `news:publishedDate` | `Blocked` | Person and organisation mentions are not yet typed as politicians or political parties. | `Hard` |
