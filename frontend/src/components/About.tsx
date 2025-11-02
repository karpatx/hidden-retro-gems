import { Title, Text, Container, Paper } from '@mantine/core'

function About() {
  return (
    <Container>
      <Title order={1} mb="lg">
        Rólunk
      </Title>

      <Paper shadow="xs" p="xl" radius="md" withBorder>
        <Text size="lg" mb="md">
          A Hidden Gem egy weboldal, amely segít felfedezni a kevésbé ismert, de méltó játékokat
          különböző konzolokon és platformokon.
        </Text>

        <Text mb="md">
          Az oldal több mint 5000 rejtett gyöngyszem gyűjteményét tartalmazza, amelyek közt
          megtalálhatók minden generáció klasszikus konzoljain elérhető játékok.
        </Text>

        <Text>
          Használd a keresési és szűrő funkciókat, hogy megtaláld a neked tetsző játékokat, vagy
          egyszerűen böngészd a teljes listát új élményekért!
        </Text>
      </Paper>

      <Paper shadow="xs" p="xl" radius="md" withBorder mt="xl">
        <Title order={3} mb="md">
          Technológiák
        </Title>
        <Text mb="xs">• Backend: FastAPI + Python</Text>
        <Text mb="xs">• Frontend: React + TypeScript</Text>
        <Text mb="xs">• UI Framework: Mantine</Text>
        <Text>• Build tools: UV, Vite</Text>
      </Paper>
    </Container>
  )
}

export default About

