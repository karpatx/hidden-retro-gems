import { useState, useEffect } from 'react'
import {
  TextInput,
  Select,
  Table,
  Container,
  Title,
  Stack,
  Group,
  Badge,
  Text,
  LoadingOverlay,
} from '@mantine/core'

interface Game {
  title: string
  manufacturer: string
  console: string
  type?: string  // "trivial" or "hidden_gem"
}

function Games() {
  const [games, setGames] = useState<Game[]>([])
  const [filteredGames, setFilteredGames] = useState<Game[]>([])
  const [manufacturers, setManufacturers] = useState<string[]>([])
  const [consoles, setConsoles] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedManufacturer, setSelectedManufacturer] = useState<string | null>(null)
  const [selectedConsole, setSelectedConsole] = useState<string | null>(null)

  useEffect(() => {
    fetchGames()
    fetchManufacturers()
    fetchConsoles()
  }, [])

  useEffect(() => {
    filterGames()
  }, [games, searchQuery, selectedManufacturer, selectedConsole])

  const fetchGames = async () => {
    try {
      const response = await fetch('http://localhost:8000/games')
      const data = await response.json()
      setGames(data.games)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching games:', error)
      setLoading(false)
    }
  }

  const fetchManufacturers = async () => {
    try {
      const response = await fetch('http://localhost:8000/manufacturers')
      const data = await response.json()
      const mfrs = data.manufacturers.map((m: any) => m.name)
      setManufacturers(mfrs)
    } catch (error) {
      console.error('Error fetching manufacturers:', error)
    }
  }

  const fetchConsoles = async () => {
    try {
      const response = await fetch('http://localhost:8000/games/consoles')
      const data = await response.json()
      setConsoles(data.consoles)
    } catch (error) {
      console.error('Error fetching consoles:', error)
    }
  }

  const filterGames = () => {
    let filtered = games

    if (searchQuery) {
      filtered = filtered.filter((game) =>
        game.title.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    if (selectedManufacturer) {
      filtered = filtered.filter(
        (game) => game.manufacturer === selectedManufacturer
      )
    }

    if (selectedConsole) {
      filtered = filtered.filter(
        (game) => game.console === selectedConsole
      )
    }

    setFilteredGames(filtered)
  }

  const rows = filteredGames.map((game, index) => (
    <Table.Tr key={index}>
      <Table.Td>{game.title}</Table.Td>
      <Table.Td>
        <Badge variant="light" color="blue">
          {game.manufacturer}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Badge variant="light" color="green">
          {game.console}
        </Badge>
      </Table.Td>
      <Table.Td>
        {game.type === "trivial" ? (
          <Badge variant="filled" color="blue" size="sm">
            Triviális
          </Badge>
        ) : (
          <Badge variant="filled" color="violet" size="sm">
            Hidden Gem
          </Badge>
        )}
      </Table.Td>
    </Table.Tr>
  ))

  return (
    <Container>
      <Title order={1} mb="lg">
        Játékok
      </Title>

      <Stack gap="md" mb="xl">
        <TextInput
          placeholder="Játék keresése..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />

        <Group grow>
          <Select
            placeholder="Gyártó kiválasztása"
            data={manufacturers}
            value={selectedManufacturer}
            onChange={setSelectedManufacturer}
            clearable
          />
          <Select
            placeholder="Konzol kiválasztása"
            data={consoles}
            value={selectedConsole}
            onChange={setSelectedConsole}
            clearable
          />
        </Group>

        <Text size="sm" c="dimmed">
          {filteredGames.length} játék található
        </Text>
      </Stack>

      <div style={{ position: 'relative' }}>
        <LoadingOverlay visible={loading} />
        <Table.ScrollContainer minWidth={800}>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Cím</Table.Th>
                <Table.Th>Gyártó</Table.Th>
                <Table.Th>Konzol</Table.Th>
                <Table.Th>Típus</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>{rows}</Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      </div>
    </Container>
  )
}

export default Games

