import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Player } from './entities/player.entity';

@Injectable()
export class PlayersService {
  constructor(
    @InjectRepository(Player)
    private readonly playersRepository: Repository<Player>,
  ) {}

  async findByUserId(userId: string): Promise<Player[]> {
    return this.playersRepository.find({
      where: { userId },
      order: { shirtNumber: 'ASC' },
    });
  }

  async countByUserId(userId: string): Promise<number> {
    return this.playersRepository.count({ where: { userId } });
  }

  async create(playerData: Partial<Player>): Promise<Player> {
    const player = this.playersRepository.create(playerData);
    return this.playersRepository.save(player);
  }
}
