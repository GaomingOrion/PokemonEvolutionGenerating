import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import os
import pandas as pd
from common import config

class getEvolutionChain:
    def __init__(self):
        self.headers = config.headers
        self.sess = requests.session()
        self.sess.headers.update(self.headers)
        self.evo_url = config.evo_url
        self.image_dir = config.image_dir

        self.data_dict = {}
        # pokemon_index -> [eng_name, type1, type2, evolution_indices]

    @staticmethod
    def parseEvoInfocard(soup):
        '''
        parse one pokemon information on the evo_page
        '''
        img_src_url = soup.find('span', class_='img-fixed img-sprite')['data-src']
        eng_name = soup.find('a', class_='ent-name').string
        small = soup.find_all('small')
        index = small[0].string[1:]
        type_lst = small[-1].find_all('a')
        type1 = type_lst[0].string
        type2 = type_lst[1].string if len(type_lst) == 2 else None

        # special form
        if len(small) == 3:
            form = small[1].string
            if index != '744':
                if form.startswith('Alolan'):
                    form = 'Alolan'
                index += '-'+form
                eng_name += '-'+form
        return index, eng_name,  type1, type2, img_src_url

    @staticmethod
    def parseDexInfocard(soup):
        index_tag = 0

    def savePokemonPair(self, head, tail=None):
        img_src_url = head[-1]
        tosave = list(head[:-1])
        if tail:
            tosave.append(tail[0])
        else:
            tosave.append('')
        if tosave[0] not in self.data_dict.keys():
            self.data_dict[tosave[0]] = tosave[1:]
            # save image
            path = self.image_dir+tosave[0]
            if not os.path.exists(path):
                os.mkdir(path)
                r = self.sess.get(img_src_url)
                img = Image.open(BytesIO(r.content))
                img.convert('1')
                img.save(path+'/normal.png')
        else:
            if tosave[-1] != '':
                if self.data_dict[tosave[0]][-1] == '':
                    self.data_dict[tosave[0]][-1] += tosave[-1]
                else:
                    self.data_dict[tosave[0]][-1] += ',' + tosave[-1]

    def parseSubChain(self, soup, init_head):
        head = init_head
        for child in soup.contents[0].children:
            if child != '\n':
                try:
                    if child['class'] == ['infocard']:
                        pokemon = self.parseEvoInfocard(child)
                        self.savePokemonPair(head, pokemon)
                        self.savePokemonPair(pokemon)
                        head = pokemon
                # special 292 Shedinja
                except KeyError:
                    head = init_head


    def parseChain(self, soup):
        head = None
        for child in soup.children:
            if child != '\n':
                if child['class'] == ['infocard']:
                    pokemon = self.parseEvoInfocard(child)
                    if head:
                        self.savePokemonPair(head, pokemon)
                        self.savePokemonPair(pokemon)
                        head = pokemon
                    else:
                        self.savePokemonPair(pokemon)
                        head = pokemon
                elif child['class'] == ['infocard-evo-split']:
                    for grandchild in child.children:
                        if grandchild['class'] == ['infocard-list-evo']:
                            self.parseSubChain(grandchild, head)

    def getExtraPokemon(self):
        '''
        get pokemons info who are not in evolution chain
        :return:
        '''


    def main(self):
        r = self.sess.get(self.evo_url)
        soup = BeautifulSoup(r.text, 'lxml')
        for chain in soup.find('main').children:
            if chain.name == 'div' and chain['class'] == ['infocard-list-evo']:
                self.parseChain(chain)
        df = pd.DataFrame.from_dict(self.data_dict, orient='index')
        df.columns = ['eng_name', 'type1', 'type2', 'evolution']
        df.to_csv('../data/evolution_chain.csv')

        self.sess.close()

    def test(self):
        r = self.sess.get(self.evo_url)
        soup = BeautifulSoup(r.text, 'lxml')
        for chain in soup.find('main').children:
            if chain.name == 'div' and chain['class'][0] == 'infocard-list-evo':
                try:
                    if chain.contents[5]['class'] == ['infocard-evo-split']:
                        return chain
                except:
                    pass


if __name__ == '__main__':
    g = getEvolutionChain()
    r = g.test()
    #r = g.main()
