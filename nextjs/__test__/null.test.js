//import Langbot  from '@/components/chat/Langbot'
//import DataResults from "@/components/chat/DataResults";

const opa = ['hi']

const nullFunc = (arr)  => {
    return arr[0]
}
 
describe('null', () => {
    it('is it null', () =>{
        expect(nullFunc(opa)).toBe('hi');
    })
})