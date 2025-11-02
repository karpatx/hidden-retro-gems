import { Routes, Route } from 'react-router-dom'
import { AppShell, Burger, Group, Title, Container, Anchor } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import Home from './components/Home'
import Games from './components/Games'
import About from './components/About'
import Manufacturers from './components/Manufacturers'
import ManufacturerDetail from './components/ManufacturerDetail'
import ManufacturerPlatformGames from './components/ManufacturerPlatformGames'
import GameDetail from './components/GameDetail'

function App() {
  const [opened, { toggle }] = useDisclosure()

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 200,
        breakpoint: 'sm',
        collapsed: { mobile: !opened, desktop: false },
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
          <Title order={2}>Hidden Gem</Title>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Group gap="xs">
          <Anchor href="/" underline="never" c="inherit">
            Főoldal
          </Anchor>
          <Anchor href="/manufacturers" underline="never" c="inherit">
            Gyártók
          </Anchor>
          <Anchor href="/games" underline="never" c="inherit">
            Játékok
          </Anchor>
          <Anchor href="/about" underline="never" c="inherit">
            Rólunk
          </Anchor>
        </Group>
      </AppShell.Navbar>

      <AppShell.Main>
        <Container size="xl">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/manufacturers" element={<Manufacturers />} />
            <Route path="/manufacturer/:name" element={<ManufacturerDetail />} />
            <Route path="/manufacturer/:name/:platform" element={<ManufacturerPlatformGames />} />
            <Route path="/game/:name" element={<GameDetail />} />
            <Route path="/games" element={<Games />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </Container>
      </AppShell.Main>
    </AppShell>
  )
}

export default App

