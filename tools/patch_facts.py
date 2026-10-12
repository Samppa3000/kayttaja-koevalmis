"""One-off: apply FAKTAT audit fixes (2026-10-12) to fi/en question text."""
import json, glob, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = {
 "ta01": {"fi.q":"Mitä yhdenvertaisuuslaki kieltää?",
          "fi.o":["Syrjinnän esimerkiksi iän, uskonnon tai vammaisuuden perusteella","Vain sukupuoleen perustuvan syrjinnän","Vain työpaikalla tapahtuvan syrjinnän","Vain Suomen kansalaisiin kohdistuvan syrjinnän"],
          "a":0,"en.q":"What does the Non-Discrimination Act prohibit?",
          "en.o":["Discrimination based on, for example, age, religion or disability","Only discrimination based on gender","Only discrimination at the workplace","Only discrimination against Finnish citizens"]},
 "hi16": {"fi.q":"Talvisodan ja jatkosodan jälkeen Suomi joutui luovuttamaan alueita Neuvostoliitolle. Satoja tuhansia ihmisiä, suurin osa karjalaisia, muutti muualle Suomeen.",
          "fi.e":"Totta. Luovutetuilta alueilta muutti noin 430 000 ihmistä. Heidät asutettiin muualle Suomeen.",
          "en.q":"After the Winter War and the Continuation War, Finland had to cede territory to the Soviet Union. Hundreds of thousands of people, most of them Karelians, moved elsewhere in Finland.",
          "en.e":"True. About 430,000 people moved from the ceded areas. They were resettled elsewhere in Finland."},
 "ar12": {"fi.q":"Minä vuonna oppivelvollisuus yleensä alkaa?",
          "fi.e":"Oppivelvollisuus alkaa yleensä sinä vuonna, jona lapsi täyttää seitsemän vuotta. Sitä ennen lapsi käy vuoden esiopetuksessa.",
          "en.q":"In which year does compulsory education usually begin?",
          "en.e":"Compulsory education usually begins in the year the child turns seven. Before that, the child attends one year of pre-primary education."},
 "ta05": {"fi.e":"Yhdenvertaisuusvaltuutettu neuvoo syrjintää kokeneita ja valvoo yhdenvertaisuuslain noudattamista. Työelämän syrjintää valvoo myös työsuojeluviranomainen.",
          "en.e":"The Non-Discrimination Ombudsman advises people who have faced discrimination and oversees the Non-Discrimination Act. Discrimination at work is also overseen by the occupational safety and health authority."},
 "po18": {"fi.q":"Mikä on otettava ensisijaisesti huomioon lasta koskevissa asioissa Suomen lain ja YK:n lapsen oikeuksien sopimuksen mukaan?",
          "fi.o0":"Aina vanhempien mielipide",
          "en.q":"Under Finnish law and the UN Convention on the Rights of the Child, what must be a primary consideration in matters concerning a child?",
          "en.o0":"Always the parents' opinion"},
 "ta14": {"fi.q":"Mitä Suomen laki sanoo seksuaalisesta häirinnästä työpaikalla?","en.q":"What does Finnish law say about sexual harassment at work?"},
 "va14": {"fi.o2":"Rajavalvonta","en.o2":"Border control"},
 "hi03": {"fi.q":"Minkä valtakunnan osa suurin osa Suomesta oli satojen vuosien ajan ennen vuotta 1809?",
          "en.q":"Which kingdom was most of Finland part of for hundreds of years before 1809?"},
 "po16": {"fi.o1":"Jos ihminen ei itse pysty huolehtimaan toimeentulostaan, hänellä on oikeus välttämättömään toimeentuloon ja huolenpitoon",
          "en.o1":"If a person cannot support themselves, they have the right to indispensable subsistence and care"},
 "va19": {"fi.e":"Totta. Asevelvollisuus koskee miehiä, jotka ovat Suomen kansalaisia. Naiset voivat hakea vapaaehtoiseen asepalvelukseen."},
 "ta13": {"fi.q":"Tyttöjen ja naisten sukuelinten silpominen (ympärileikkaus) on Suomessa rikos.",
          "fi.e":"Totta. Vuodesta 2025 alkaen silpominen on rikoslaissa oma rikoksensa. Se on rangaistava myös, jos se tehdään ulkomailla tai vanhempien luvalla.",
          "en.q":"Female genital mutilation (of girls and women) is a crime in Finland.",
          "en.e":"True. Since 2025, female genital mutilation has been a separate crime in the Criminal Code. It is punishable even if done abroad or with the parents' permission."},
 "va09": {"fi.e":"Totta. EU-maan, Islannin ja Norjan kansalainen voi äänestää, jos hänen kotikuntansa on Suomessa. Muun maan kansalaisella kotikunnan pitää olla Suomessa vähintään kaksi vuotta.",
          "en.e":"True. Citizens of EU countries, Iceland and Norway can vote if their municipality of residence is in Finland. Citizens of other countries must have had a municipality of residence in Finland for at least two years."},
 "ku14": {"fi.e":"Suomessa on vähän yli 5,6 miljoonaa asukasta.","en.e":"Finland has just over 5.6 million inhabitants."},
 "ar13": {"fi.e":"Totta. Suomessa kaikki oppilaat ovat saaneet maksuttoman kouluruoan vuodesta 1948.","en.e":"True. All pupils in Finland have received free school meals since 1948."},
 "ar10": {"fi.e":"Muuttoilmoitus on tehtävä viimeistään viikon kuluessa muutosta. Ilmoitus tehdään Digi- ja väestötietovirastolle (DVV), ja tieto välittyy myös muille viranomaisille.",
          "en.e":"You must make a notification of move within a week of moving. You make it to the Digital and Population Data Services Agency (DVV), and the information is passed on to other authorities."},
 "po03": {"fi.e":"Väärin. Kokoontumisvapaus kuuluu jokaiselle. Lupaa ei tarvita, mutta ulkona yleisellä paikalla järjestettävästä mielenosoituksesta tehdään ennakkoilmoitus poliisille.",
          "en.e":"False. Everyone has freedom of assembly. No permit is needed, but the police must be notified in advance of a demonstration held outdoors in a public place."},
 "po07": {"fi.e":"Oppivelvollisuus päättyy, kun nuori täyttää 18 vuotta tai suorittaa toisen asteen tutkinnon. Peruskoulun jälkeen nuori jatkaa esimerkiksi lukioon tai ammatilliseen koulutukseen.",
          "en.e":"Compulsory education ends when the young person turns 18 or completes an upper secondary qualification. After basic school, young people continue to general upper secondary school or vocational education, for example."},
 "ku13": {"fi.e":"Helsinki on Suomen pääkaupunki vuodesta 1812. Sitä ennen Turku oli Suomen tärkein kaupunki ja hallinnon keskus.",
          "en.e":"Helsinki has been the capital of Finland since 1812. Before that, Turku was Finland's most important city and administrative centre."},
 "va18": {"fi.q":"Kansalaisaloite menee eduskunnan käsiteltäväksi, jos sillä on tarpeeksi allekirjoituksia. Montako allekirjoitusta tarvitaan?",
          "fi.e":"Vähintään 50 000 äänioikeutetun Suomen kansalaisen pitää allekirjoittaa aloite kuuden kuukauden aikana.",
          "en.q":"A citizens' initiative goes to Parliament if it has enough signatures. How many signatures are needed?",
          "en.e":"At least 50,000 Finnish citizens entitled to vote must sign the initiative within six months."},
 "va13": {"fi.q":"Kuka järjestää sosiaali- ja terveyspalvelut sekä pelastustoimen? (Helsinki on poikkeus.)",
          "en.q":"Who organises social and health services and rescue services? (Helsinki is an exception.)"},
 "po11": {"fi.q":"Perustuslain mukaan joillakin ryhmillä on oikeus ylläpitää ja kehittää omaa kieltään ja kulttuuriaan. Mitkä ryhmät perustuslaki mainitsee?"},
 "po14": {"fi.q":"Euroopan ihmisoikeussopimus suojaa ihmisoikeuksia. Mihin voi lopulta valittaa, jos Suomi on loukannut näitä oikeuksia?"},
 "ta06": {"fi.q":"Kuka valvoo tasa-arvolakia, joka koskee naisten ja miesten tasa-arvoa?"},
 "ar09": {"fi.q":"Mikä on työaikalain mukaan säännöllinen työaika enintään?"},
 "hi14": {"fi.q":"Ketä kutsutaan suomen kirjakielen isäksi? Hän julkaisi ensimmäisen suomenkielisen aapisen 1500-luvulla."},
 "ku06": {"fi.e":"Evankelis-luterilaisen ja ortodoksisen kirkon asemasta on omat lakinsa. Suomessa on kuitenkin uskonnonvapaus."},
 "ar02": {"fi.o2":"100","en.o2":"100"},
 "va17": {"en.e":"The Parliamentary Ombudsman ensures that authorities comply with the law. Anyone can file a complaint, and it is free."},
}
done=set()
for f in glob.glob(os.path.join(ROOT,"data","q_*.json")):
    d=json.load(open(f,encoding="utf-8")); ch=False
    for q in d:
        p=P.get(q["id"])
        if not p: continue
        for k,v in p.items():
            if k=="a": q["a"]=v
            else:
                L,fld=k.split(".")
                if fld.startswith("o") and len(fld)==2: q[L]["o"][int(fld[1])]=v
                else: q[L][fld]=v
        done.add(q["id"]); ch=True
    if ch: json.dump(d,open(f,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("patched",len(done),"missing",set(P)-done)
