import { Module } from '@nestjs/common';
import { SeedService } from './seed.service';
import { UsersModule } from '../users/users.module';
import { PlayersModule } from '../players/players.module';

@Module({
  imports: [UsersModule, PlayersModule],
  providers: [SeedService],
})
export class SeedModule {}
