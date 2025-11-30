import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Container,
  Title,
  Card,
  Text,
  Badge,
  Stack,
  Group,
  LoadingOverlay,
  Anchor,
  Breadcrumbs,
  Grid,
  Image,
} from '@mantine/core'
import { toSlug } from '../utils/slug'

interface Game {
  title: string
  manufacturer: string
  console: string
  type?: string  // "trivial" or "hidden_gem"
}

interface GameWithThumbnail extends Game {
  thumbnail?: string | null
}

function ManufacturerPlatformGames() {
  const { name, platform } = useParams<{ name: string; platform: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<{
    manufacturer: string
    platform: string
    games: GameWithThumbnail[]
    total: number
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [thumbnails, setThumbnails] = useState<{ [key: string]: string | null }>({})
  const [systemImage, setSystemImage] = useState<string | null>(null)

  useEffect(() => {
    if (name && platform) {
      fetchGamesBySlug(name, platform)
    }
  }, [name, platform])

  const fetchGamesBySlug = async (mfrSlug: string, platformSlug: string) => {
    try {
      // Get all manufacturers and find the one matching the slug
      const manufacturersResponse = await fetch('http://localhost:8000/manufacturers')
      const manufacturersData = await manufacturersResponse.json()
      
      const manufacturer = manufacturersData.manufacturers.find((mfr: any) => 
        toSlug(mfr.name) === mfrSlug
      )
      
      if (manufacturer) {
        // Find platform matching the slug
        const platform = manufacturer.platforms.find((plt: string) => 
          toSlug(plt) === platformSlug
        )
        
        if (platform) {
          await fetchGames(manufacturer.name, platform)
        } else {
          setLoading(false)
        }
      } else {
        setLoading(false)
      }
    } catch (error) {
      console.error('Error fetching games by slug:', error)
      setLoading(false)
    }
  }

  const fetchGames = async (mfrName: string, platformName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/manufacturer/${encodeURIComponent(mfrName)}/${encodeURIComponent(platformName)}`)
      const data = await response.json()
      setData(data)
      
      // Fetch system image
      try {
        const systemImgResponse = await fetch(
          `http://localhost:8000/systems/${encodeURIComponent(platformName)}/image`
        )
        const systemImgData = await systemImgResponse.json()
        setSystemImage(systemImgData.image)
      } catch (error) {
        setSystemImage(null)
      }
      
      // Fetch thumbnails for all games
      const thumbnailPromises = data.games.map(async (game: Game) => {
        try {
          const thumbResponse = await fetch(
            `http://localhost:8000/games/${encodeURIComponent(game.title)}/thumbnail?console=${encodeURIComponent(game.console)}`
          )
          const thumbData = await thumbResponse.json()
          return { title: game.title, thumbnail: thumbData.thumbnail }
        } catch (error) {
          return { title: game.title, thumbnail: null }
        }
      })
      
      const thumbResults = await Promise.all(thumbnailPromises)
      const thumbMap: { [key: string]: string | null } = {}
      thumbResults.forEach((result) => {
        thumbMap[result.title] = result.thumbnail
      })
      setThumbnails(thumbMap)
      
      setLoading(false)
    } catch (error) {
      console.error('Error fetching platform games:', error)
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

  if (loading) {
    return (
      <Container>
        <LoadingOverlay visible={loading} />
      </Container>
    )
  }

  if (!data) {
    return (
      <Container>
        <Title order={2}>Játékok nem találhatók</Title>
      </Container>
    )
  }

  const items = [
    { title: 'Gyártók', href: '/manufacturers' },
    { title: data.manufacturer, href: `/manufacturer/${toSlug(data.manufacturer)}` },
    { title: data.platform, href: '#' },
  ].map((item, index) => (
    <Anchor key={index} onClick={() => navigate(item.href)}>
      {item.title}
    </Anchor>
  ))

  return (
    <Container>
      <Breadcrumbs mb="lg">{items}</Breadcrumbs>

      {systemImage && (
        <Group justify="center" mb="lg">
          <Image
            src={`http://localhost:8000${systemImage}`}
            height={200}
            alt={data.platform}
            fallbackSrc="https://via.placeholder.com/400x200"
            fit="contain"
          />
        </Group>
      )}

      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1} mb="xs">
            {data.manufacturer} - {data.platform}
          </Title>
          <Text c="dimmed">ABC sorrendben</Text>
        </div>
        <Badge variant="light" color={getColorForManufacturer(data.manufacturer)} size="lg">
          {data.total} játék
        </Badge>
      </Group>

      <div style={{ position: 'relative' }}>
        <LoadingOverlay visible={loading} />
        <Grid gutter="md">
          {data.games.map((game, index) => (
            <Grid.Col key={index} span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
              <Anchor
                onClick={() => navigate(`/manufacturer/${toSlug(game.manufacturer)}/${toSlug(game.console)}/game/${toSlug(game.title)}`)}
                underline="never"
              >
                <Card
                  shadow="sm"
                  padding="lg"
                  radius="md"
                  withBorder
                  style={{ height: '100%', cursor: 'pointer' }}
                  className="game-card"
                >
                  <Card.Section>
                    <Image
                      src={
                        thumbnails[game.title] 
                          ? `http://localhost:8000${thumbnails[game.title]}` 
                          : `https://via.placeholder.com/400x300?text=${encodeURIComponent(game.title)}`
                      }
                      height={160}
                      alt={game.title}
                      fallbackSrc="https://via.placeholder.com/400x300"
                    />
                  </Card.Section>

                  <Stack gap="xs" mt="md">
                    <Text fw={600} size="sm" lineClamp={2}>
                      {game.title}
                    </Text>
                    <Group gap="xs">
                      <Badge variant="light" color={getColorForManufacturer(data.manufacturer)} size="sm">
                        {game.console}
                      </Badge>
                      {game.type === "trivial" ? (
                        <Badge variant="filled" color="blue" size="sm">
                          Triviális
                        </Badge>
                      ) : (
                        <Badge variant="filled" color="violet" size="sm">
                          Hidden Gem
                        </Badge>
                      )}
                    </Group>
                  </Stack>
                </Card>
              </Anchor>
            </Grid.Col>
          ))}
        </Grid>
      </div>
    </Container>
  )
}

export default ManufacturerPlatformGames

