import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule } from './config/config.module';
import { AuthModule } from './auth/auth.module';
import { UsersModule } from './users/users.module';
import { PlayersModule } from './players/players.module';
import { SeedModule } from './seed/seed.module';
import { User } from './users/entities/user.entity';
import { Player } from './players/entities/player.entity';

@Module({
  imports: [
    ConfigModule,
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.POSTGRES_HOST || 'postgres',
      port: parseInt(process.env.POSTGRES_PORT || '5432', 10),
      username: process.env.POSTGRES_USER || 'fm_user',
      password: process.env.POSTGRES_PASSWORD || 'fm_password',
      database: process.env.POSTGRES_DB || 'football_manager',
      entities: [User, Player],
      synchronize: true,
    }),
    AuthModule,
    UsersModule,
    PlayersModule,
    SeedModule,
  ],
})
export class AppModule {}
