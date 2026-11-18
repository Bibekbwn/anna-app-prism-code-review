import type { ComponentProps } from 'react'
import type { PageId } from './data'
import { NewReviewPage, ReviewHistoryPage, ReviewResultsPage } from './review-pages'
import { CodeComparePage, PreferencesPage, SnippetTemplatesPage } from './tools-pages'

type PageProps = {
  activePage: PageId
  newReview: ComponentProps<typeof NewReviewPage>
  results: ComponentProps<typeof ReviewResultsPage>
  history: ComponentProps<typeof ReviewHistoryPage>
  templates: ComponentProps<typeof SnippetTemplatesPage>
  compare: ComponentProps<typeof CodeComparePage>
  preferences: ComponentProps<typeof PreferencesPage>
}

export function PrismPageContent({
  activePage,
  newReview,
  results,
  history,
  templates,
  compare,
  preferences,
}: PageProps) {
  switch (activePage) {
    case 'new':
      return <NewReviewPage {...newReview} />
    case 'results':
      return <ReviewResultsPage {...results} />
    case 'history':
      return <ReviewHistoryPage {...history} />
    case 'templates':
      return <SnippetTemplatesPage {...templates} />
    case 'compare':
      return <CodeComparePage {...compare} />
    case 'preferences':
      return <PreferencesPage {...preferences} />
    default:
      return <NewReviewPage {...newReview} />
  }
}
