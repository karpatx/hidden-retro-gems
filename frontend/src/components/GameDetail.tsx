import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Container,
  Title,
  Text,
  Badge,
  Stack,
  Group,
  LoadingOverlay,
  Anchor,
  Breadcrumbs,
  Grid,
  Image,
  Card,
  Paper,
  Divider,
  Button,
} from '@mantine/core'

interface Game {
  title: string
  manufacturer: string
  console: string
}

interface GameDetails {
  title: string
  description: string
  images: string[]
  image_count: number
}

function GameDetail() {
  const { name } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const [game, setGame] = useState<Game | null>(null)
  const [gameDetails, setGameDetails] = useState<GameDetails | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (name) {
      const decodedTitle = decodeURIComponent(name)
      fetchGame(decodedTitle)
    }
  }, [name])

  const fetchGame = async (gameTitle: string) => {
    try {
      // Search for the game
      const response = await fetch(`http://localhost:8000/games/search?q=${encodeURIComponent(gameTitle)}`)
      const data = await response.json()
      
      // Find exact match
      const foundGame = data.games.find((g: Game) => g.title === gameTitle)
      
      if (foundGame) {
        setGame(foundGame)
        
        // Fetch game details (description + images)
        try {
          const detailsResponse = await fetch(
            `http://localhost:8000/games/${encodeURIComponent(gameTitle)}/details?console=${encodeURIComponent(foundGame.console)}`
          )
          const detailsData = await detailsResponse.json()
          setGameDetails(detailsData)
        } catch (error) {
          console.error('Error fetching game details:', error)
        }
      }
      setLoading(false)
    } catch (error) {
      console.error('Error fetching game:', error)
      setLoading(false)
    }
  }

  const getColorForManufacturer = (mfrName: string): string => {
    const colors: { [key: string]: string } = {
      Nintendo: 'red',
      Sony: 'blue',
      Sega: 'teal',
      Microsoft: 'green',
      SNK: 'orange',
      NEC: 'purple',
      PC: 'grape',
      Commodore: 'cyan',
      Sinclair: 'yellow',
      'Pico-8': 'pink',
    }
    return colors[mfrName] || 'gray'
  }


  const generateTags = (title: string): string[] => {
    const allTags = ['Action', 'Adventure', 'RPG', 'Platformer', 'Puzzle', 'Strategy', 'Shooter', 'Racing', 'Simulation', 'Fighting', 'Hidden Gem', 'Cult Classic', 'Retro Gaming', 'Indie']
    const hash = title.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    const numTags = 3 + (hash % 4)
    const selectedTags = []
    let currentHash = hash
    
    for (let i = 0; i < numTags; i++) {
      selectedTags.push(allTags[currentHash % allTags.length])
      currentHash = Math.floor(currentHash / allTags.length)
    }
    
    return [...new Set(selectedTags)]
  }

  if (loading) {
    return (
      <Container>
        <LoadingOverlay visible={loading} />
      </Container>
    )
  }

  if (!game) {
    return (
      <Container>
        <Title order={2}>Játék nem található</Title>
      </Container>
    )
  }

  const items = [
    { title: 'Gyártók', href: '/manufacturers' },
    { title: game.manufacturer, href: `/manufacturer/${game.manufacturer}` },
    { title: game.console, href: `/manufacturer/${game.manufacturer}/${game.console}` },
    { title: game.title, href: '#' },
  ].map((item, index) => (
    <Anchor key={index} onClick={() => navigate(item.href)}>
      {item.title}
    </Anchor>
  ))

  const tags = generateTags(game.title)
  const description = gameDetails?.description || `${game.title} egy játék a ${game.console} platformon.`
  const mainImage = gameDetails?.images && gameDetails.images.length > 0 
    ? `http://localhost:8000${gameDetails.images[0]}` 
    : `https://via.placeholder.com/800x600?text=${encodeURIComponent(game.title)}`
  const galleryImages = gameDetails?.images || []

  return (
    <Container>
      <Breadcrumbs mb="lg">{items}</Breadcrumbs>

      <Grid gutter="xl">
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card shadow="md" padding="lg" radius="md" withBorder>
            <Image
              src={mainImage}
              radius="md"
              alt={game.title}
              fallbackSrc="https://via.placeholder.com/800x600"
            />
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack gap="md">
            <div>
              <Title order={1} mb="xs">{game.title}</Title>
              <Group gap="xs">
                <Badge variant="light" color={getColorForManufacturer(game.manufacturer)} size="lg">
                  {game.manufacturer}
                </Badge>
                <Badge variant="light" color="blue" size="lg">
                  {game.console}
                </Badge>
              </Group>
            </div>

            <Divider />

            <div>
              <Title order={3} mb="sm">Rövid leírás</Title>
              <Text>{description}</Text>
            </div>

            <div>
              <Title order={3} mb="sm">Műfaj</Title>
              <Group gap="xs">
                {tags.map((tag, idx) => (
                  <Badge key={idx} variant="outline" size="sm">
                    {tag}
                  </Badge>
                ))}
              </Group>
            </div>

            <Group mt="lg">
              <Button
                variant="light"
                onClick={() => navigate(`/manufacturer/${game.manufacturer}/${game.console}`)}
              >
                ← Vissza a platform listához
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/manufacturer/${game.manufacturer}`)}
              >
                Több játék {game.manufacturer}-tól
              </Button>
            </Group>
          </Stack>
        </Grid.Col>

        {galleryImages.length > 0 && (
          <Grid.Col span={12}>
            <Paper shadow="sm" p="md" radius="md" withBorder>
              <Title order={3} mb="sm">Képek</Title>
              <Grid gutter="md">
                {galleryImages.map((imgPath, idx) => (
                  <Grid.Col key={idx} span={{ base: 12, sm: 6, md: 3 }}>
                    <Image
                      src={`http://localhost:8000${imgPath}`}
                      radius="md"
                      alt={`${game.title} ${idx + 1}`}
                      fallbackSrc="https://via.placeholder.com/400x300"
                    />
                  </Grid.Col>
                ))}
              </Grid>
            </Paper>
          </Grid.Col>
        )}
      </Grid>
    </Container>
  )
}

export default GameDetail


