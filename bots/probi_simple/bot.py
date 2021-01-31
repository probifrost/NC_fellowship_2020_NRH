
__author__ = '남현준'

import time

import sc2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.buff_id import BuffId


class Bot(sc2.BotAI):
    """
    밴시, 해병만 뽑는 봇
    밴시는 적 조우시 은폐한다.
    해병은 적 조우시 스팀팩을 사용한다. (이전 코드 재사용)
    
    """
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.build_order = list() # 생산할 유닛 목록

    def on_start(self):
        """
        새로운 게임마다 초기화
        """
        self.build_order = list()
        self.evoked = dict()

    async def on_step(self, iteration: int):       
        actions = list()
        #
        # 빌드 오더 생성
        # 
        if len(self.build_order) == 0:
            for _ in range(5):
                self.build_order.append(UnitTypeId.MARINE)
            self.build_order.append(UnitTypeId.BANSHEE)

        #
        # 사령부 명령 생성
        #
        ccs = self.units(UnitTypeId.COMMANDCENTER)  # 전체 유닛에서 사령부 검색
        ccs = ccs.idle  # 실행중인 명령이 없는 사령부 검색
        if ccs.exists:  # 사령부가 하나이상 존재할 경우
            cc = ccs.first  # 첫번째 사령부 선택
            if self.can_afford(self.build_order[0]) and self.time - self.evoked.get((cc.tag, 'train'), 0) > 1.0:
                # 해당 유닛 생산 가능하고, 마지막 명령을 발행한지 1초 이상 지났음
                actions.append(cc.train(self.build_order[0]))  # 첫 번째 유닛 생산 명령 
                del self.build_order[0]  # 빌드오더에서 첫 번째 유닛 제거
                self.evoked[(cc.tag, 'train')] = self.time

        #
        # 해병 명령 생성
        #
        marines = self.units(UnitTypeId.MARINE)  # 해병 검색
        for marine in marines:
            enemy_cc = self.enemy_start_locations[0]  # 적 시작 위치
            enemy_unit = self.enemy_start_locations[0]
            if self.known_enemy_units.exists:
                enemy_unit = self.known_enemy_units.closest_to(marine)  # 가장 가까운 적 유닛

            # 적 사령부와 가장 가까운 적 유닛중 더 가까운 것을 목표로 공격 명령 생성
            if marine.distance_to(enemy_cc) < marine.distance_to(enemy_unit):
                target = enemy_cc
            else:
                target = enemy_unit
            actions.append(marine.attack(target))

            if marine.distance_to(target) < 15:
                # 해병과 목표의 거리가 15이하일 경우 스팀팩 사용
                if not marine.has_buff(BuffId.STIMPACK) and marine.health_percentage > 0.5:
                    # 현재 스팀팩 사용중이 아니며, 체력이 50% 이상
                    if self.time - self.evoked.get((marine.tag, AbilityId.EFFECT_STIM), 0) > 1.0:
                        # 1초 이전에 스팀팩을 사용한 적이 없음
                        actions.append(marine(AbilityId.EFFECT_STIM))
                        self.evoked[(marine.tag, AbilityId.EFFECT_STIM)] = self.time

        #
        # 밴시 명령 생성
        #
        banshees = self.units(UnitTypeId.BANSHEE)  # 의료선 검색
        for banshee in banshees:
            enemy_cc = self.enemy_start_locations[0]  # 적 시작 위치
            enemy_unit = self.enemy_start_locations[0]
            if self.known_enemy_units.exists:
                enemy_unit = self.known_enemy_units.closest_to(banshee)  # 가장 가까운 적 유닛
            else:
                target = enemy_unit
            actions.append(banshee.attack(target))

            if banshee.distance_to(target) < 10:                                                                        # 밴시와 목표의 거리가 10이하일 경우 은폐장 사용
                if not banshee.has_buff(BuffId.BANSHEECLOAK) and banshee.energy > 50:                                   # 현재 은폐장 사용중이 아니며, 에너지 50 이상인 경우
                        actions.append(banshee(AbilityId.BEHAVIOR_CLOAKON_BANSHEE))
                        self.evoked[(banshee.tag, AbilityId.BEHAVIOR_CLOAKON_BANSHEE)] = self.time

        await self.do_actions(actions)

