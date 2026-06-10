import { Controller, Get, Req, UseGuards } from '@nestjs/common';
import { Request } from 'express';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { PlayersService } from './players.service';
import { UsersService } from '../users/users.service';

interface AuthenticatedRequest extends Request {
  user: {
    userId: string;
    email: string;
  };
}

@Controller('players')
export class PlayersController {
  constructor(
    private readonly playersService: PlayersService,
    private readonly usersService: UsersService,
  ) {}

  @Get('my-team')
  @UseGuards(JwtAuthGuard)
  async getMyTeam(@Req() req: AuthenticatedRequest) {
    const user = await this.usersService.findById(req.user.userId);
    const players = await this.playersService.findByUserId(req.user.userId);

    return {
      teamName: user?.teamName ?? 'Meu Time',
      players,
    };
  }
}
