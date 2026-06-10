import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { UsersService } from '../users/users.service';
import { PlayersService } from '../players/players.service';
import { PlayerPosition } from '../players/entities/player.entity';

const TEST_USER_EMAIL = 'admin@fm.local';
const TEST_USER_PASSWORD = 'admin123';
const TEST_TEAM_NAME = 'FC Cursor';

interface SeedPlayer {
  name: string;
  position: PlayerPosition;
  shirtNumber: number;
  age: number;
  nationality: string;
  overall: number;
}

const SEED_PLAYERS: SeedPlayer[] = [
  { name: 'Marco Silva', position: PlayerPosition.GK, shirtNumber: 1, age: 28, nationality: 'Portugal', overall: 82 },
  { name: 'Lucas Fernandez', position: PlayerPosition.GK, shirtNumber: 13, age: 24, nationality: 'Argentina', overall: 74 },
  { name: 'Henrik Dahl', position: PlayerPosition.GK, shirtNumber: 25, age: 19, nationality: 'Denmark', overall: 65 },
  { name: 'James Whitmore', position: PlayerPosition.RB, shirtNumber: 2, age: 26, nationality: 'England', overall: 79 },
  { name: 'Diego Morales', position: PlayerPosition.RB, shirtNumber: 22, age: 21, nationality: 'Spain', overall: 72 },
  { name: 'Antoine Dubois', position: PlayerPosition.LB, shirtNumber: 3, age: 27, nationality: 'France', overall: 80 },
  { name: 'Erik Lindqvist', position: PlayerPosition.LB, shirtNumber: 15, age: 23, nationality: 'Sweden', overall: 75 },
  { name: 'Carlos Mendes', position: PlayerPosition.CB, shirtNumber: 4, age: 30, nationality: 'Brazil', overall: 83 },
  { name: 'Nikolai Petrov', position: PlayerPosition.CB, shirtNumber: 5, age: 29, nationality: 'Russia', overall: 81 },
  { name: 'Kwame Osei', position: PlayerPosition.CB, shirtNumber: 6, age: 25, nationality: 'Ghana', overall: 77 },
  { name: 'Matteo Rossi', position: PlayerPosition.CB, shirtNumber: 24, age: 20, nationality: 'Italy', overall: 70 },
  { name: 'Thomas Becker', position: PlayerPosition.CDM, shirtNumber: 8, age: 28, nationality: 'Germany', overall: 82 },
  { name: 'Yuki Tanaka', position: PlayerPosition.CDM, shirtNumber: 14, age: 26, nationality: 'Japan', overall: 78 },
  { name: 'Andreas Christou', position: PlayerPosition.CM, shirtNumber: 10, age: 27, nationality: 'Greece', overall: 84 },
  { name: 'Felipe Costa', position: PlayerPosition.CM, shirtNumber: 16, age: 24, nationality: 'Brazil', overall: 76 },
  { name: 'Oliver Hughes', position: PlayerPosition.CM, shirtNumber: 18, age: 22, nationality: 'Wales', overall: 73 },
  { name: 'Rafael Santos', position: PlayerPosition.CAM, shirtNumber: 7, age: 25, nationality: 'Portugal', overall: 85 },
  { name: 'Ibrahim Al-Hassan', position: PlayerPosition.CAM, shirtNumber: 20, age: 23, nationality: 'Morocco', overall: 77 },
  { name: 'Lucas Berg', position: PlayerPosition.LW, shirtNumber: 11, age: 26, nationality: 'Netherlands', overall: 83 },
  { name: 'Samuel Okonkwo', position: PlayerPosition.LW, shirtNumber: 17, age: 21, nationality: 'Nigeria', overall: 74 },
  { name: 'Victor Andersson', position: PlayerPosition.RW, shirtNumber: 9, age: 28, nationality: 'Sweden', overall: 86 },
  { name: 'Mateo Garcia', position: PlayerPosition.RW, shirtNumber: 19, age: 22, nationality: 'Colombia', overall: 75 },
  { name: 'Stefan Novak', position: PlayerPosition.ST, shirtNumber: 12, age: 29, nationality: 'Croatia', overall: 87 },
  { name: 'Emmanuel Koffi', position: PlayerPosition.ST, shirtNumber: 21, age: 24, nationality: 'Ivory Coast', overall: 79 },
  { name: 'Pierre Martin', position: PlayerPosition.ST, shirtNumber: 23, age: 19, nationality: 'France', overall: 68 },
  { name: 'David Kowalski', position: PlayerPosition.ST, shirtNumber: 27, age: 32, nationality: 'Poland', overall: 80 },
];

@Injectable()
export class SeedService implements OnModuleInit {
  private readonly logger = new Logger(SeedService.name);

  constructor(
    private readonly usersService: UsersService,
    private readonly playersService: PlayersService,
  ) {}

  async onModuleInit() {
    await this.seed();
  }

  private async seed() {
    this.logger.log('Running database seed...');

    let user = await this.usersService.findByEmail(TEST_USER_EMAIL);

    if (!user) {
      user = await this.usersService.create(
        TEST_USER_EMAIL,
        TEST_USER_PASSWORD,
        TEST_TEAM_NAME,
      );
      this.logger.log(`Created test user: ${TEST_USER_EMAIL}`);
    } else {
      this.logger.log(`Test user already exists: ${TEST_USER_EMAIL}`);
    }

    const existingCount = await this.playersService.countByUserId(user.id);

    if (existingCount > 0) {
      this.logger.log(`Players already seeded (${existingCount} players)`);
      return;
    }

    for (const player of SEED_PLAYERS) {
      await this.playersService.create({
        ...player,
        userId: user.id,
      });
    }

    this.logger.log(`Seeded ${SEED_PLAYERS.length} players for ${TEST_TEAM_NAME}`);
  }
}
