import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from './App'
import i18n from './i18n'

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App shell', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })

  it('renders the 13 navigation links', () => {
    renderAt('/')
    expect(screen.getByRole('navigation', { name: 'Main' }).querySelectorAll('a')).toHaveLength(13)
  })

  it('labels unimplemented modules explicitly (no fake features)', () => {
    renderAt('/electrical')
    expect(screen.getByRole('status')).toHaveTextContent('Not implemented yet')
  })

  it('switches language to French', async () => {
    renderAt('/library')
    await userEvent.selectOptions(screen.getByLabelText('Language'), 'fr')
    expect(await screen.findByRole('heading', { name: 'Bibliothèque de composants' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Pas encore implémenté')
  })
})
