use "stream.sig";
open SMLofNJ.Susp;

structure Stream: STREAM =
struct

  exception SHd and STl and Nth

  datatype 'a streamCell = Cons of 'a * 'a stream | Nil
  withtype 'a stream = 'a streamCell susp

  (* will be useful for findOne *)
  fun headMaybe s =
    case force s of
      Cons (x, _) => SOME x
    | Nil => NONE

  fun sHd (s: 'a stream) : 'a =
    case headMaybe s of
      SOME x => x
    | NONE => raise SHd

  fun sTl (s: 'a stream) : 'a stream =
    case force s of
      Cons (_, xs) => xs
    | Nil => raise STl

  infixr 5 ++

  fun s1 ++ s2 =
    case force s1 of
      Cons (x, xs) => delay (fn () => Cons (x, (xs ++ s2)))
    | Nil => s2

  (* create a constant stream of x elements, i.e. x, x, x, x, ... *)
  fun constStream x = delay (fn () => Cons (x, constStream x))

  fun sMap f s =
    case force s of
      Cons (x, xs) => delay (fn () => Cons (f x, sMap f xs))
    | Nil => delay (fn () => Nil)

  fun from n = delay (fn () => Cons (n, from (n + 1)))

  (* create a stream by applying f to 0, 1, 2, ..., i.e. f 0, f 1, f 2, ... *)
  fun mkStream f = sMap f (from 0)

  fun sDrop n s =
    if n <= 0 then
      s
    else
      case force s of
        Cons (_, xs) => sDrop (n - 1) xs
      | Nil => delay (fn () => Nil)

  (* will be useful for splice *)
  fun sTakeRev n s acc =
    if n <= 0 then
      acc
    else
      case force s of
        Cons (x, xs) => sTakeRev (n - 1) xs (x :: acc)
      | Nil => rev acc

  fun sTake n s = rev (sTakeRev n s [])

  fun zip (s1, s2) =
    case (force s1, force s2) of
      (Cons (x, xs), Cons (y, ys)) =>
        delay (fn () => Cons ((x, y), zip (xs, ys)))
    | _ => delay (fn () => Nil)

  fun unzip (s: ('a * 'b) stream) = (sMap #1 s, sMap #2 s)

  fun takeExactly r 0 s acc = if r then rev acc else acc
    | takeExactly r n s acc = 
        case force s of
          Cons (x, xs) => takeExactly r (n - 1) xs (x :: acc)
        | Nil => []

  fun fromList xs = foldr (fn (x, acc) => delay (fn () => Cons (x, acc))) (delay (fn () => Nil)) xs

  (* create a stream of all possible pairs of elements from s1 and s2 *)
  fun splice (s1, s2) =
    let
      fun aux s1 s2 n =
        let 
          val segment = zip ((fromList (takeExactly false n s1 [])), (fromList (takeExactly true n s2 [])))
        in
          case force segment of
            Nil => delay (fn () => Nil)
          | _ => segment ++ aux s1 s2 (n + 1)
        end
    in
      aux s1 s2 0
    end

  fun filter f s =
    case force s of
      Cons (x, xs) =>
        (case f x of
           SOME y => delay (fn () => Cons (y, filter f xs))
         | NONE => filter f xs)
    | Nil => delay (fn () => Nil)

  fun find p s = filter (fn x => if p x then SOME x else NONE) s

  fun remove p s = filter (fn x => if p x then NONE else SOME x) s

  fun findOne p s = headMaybe (find p s)

  fun flatten ss = 
    case force ss of
      Cons (s, ss') => s ++ flatten ss'
    | Nil => delay (fn () => Nil)
    
  fun nth n s =
    case force (sDrop n s) of
      Cons (x, _) => x
    | Nil => raise Nth

  fun takeWhile p s =
    case force s of
      Cons (x, xs) =>
        if p x then delay (fn () => Cons (x, takeWhile p xs))
        else delay (fn () => Nil)
    | Nil => delay (fn () => Nil)

  fun prefix p s = takeWhile p s

  fun dropWhile p s =
    case force s of
      Cons (x, xs) =>
        if p x then dropWhile p xs
        else s
    | Nil => delay (fn () => Nil)

  fun suffix p s = dropWhile p s

  fun split n s = (fromList (sTake n s), sDrop n s)

  fun splitp p s = (prefix p s, suffix p s)
end;
